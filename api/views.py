import os
import re
import logging
import difflib
from functools import lru_cache
from django.conf import settings
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
import pandas as pd

_cached_df = None

def parse_price(value):
    if value is None:
        return None
    try:
        return float(value)
    except:
        s = str(value)
        if "-" in s:
            try:
                parts = [float(x) for x in s.split("-")]
                return sum(parts) / len(parts)
            except:
                return None
        s = re.sub(r"[^\d.]", "", s)
        try:
            return float(s)
        except:
            return None

def detect_price_cols(df):
    return [
        col for col in df.columns
        if any(x in col.lower() for x in ["rate", "price", "prevailing"])
    ]

def fuzzy_match_location(query_loc, locations, threshold=0.8):
    matches = difflib.get_close_matches(query_loc, locations, n=1, cutoff=threshold)
    return matches[0] if matches else None

def generate_mock_summary(area, price_cols, location_name, last_n=None):
    area = area.sort_values("year")
    if last_n:
        max_year = int(area["year"].max())
        area = area[area["year"] > max_year - last_n]

    demand_vals = area["demand"].dropna().tolist()
    avg_price_vals = []

    for col in price_cols:
        prices = area[col].dropna().map(parse_price).dropna().tolist()
        avg_price_vals.extend(prices)

    demand_trend = ""
    if len(demand_vals) > 1:
        demand_trend = (
            "rising" if demand_vals[-1] > demand_vals[0]
            else "falling" if demand_vals[-1] < demand_vals[0]
            else "stable"
        )
    elif demand_vals:
        demand_trend = "steady"

    if avg_price_vals:
        pct = ((avg_price_vals[-1] - avg_price_vals[0]) / avg_price_vals[0]) * 100
        price_trend = f"{pct:.1f}% average change over period"
    else:
        price_trend = "No price data available"

    return (
        f"{location_name.title()} has shown {price_trend} in prices, "
        f"with demand {demand_trend} over the past {last_n or 'all'} years."
    )

@lru_cache(maxsize=1)
def load_dataframe():
    global _cached_df
    if _cached_df is not None:
        return _cached_df

    excel_path = os.path.join(settings.BASE_DIR, "real_estate.xlsx")
    if not os.path.exists(excel_path):
        return None

    try:
        df = pd.read_excel(excel_path)
        df.columns = (
            df.columns.astype(str).str.strip().str.lower()
            .str.replace(" ", "_").str.replace("-", "_")
        )

        if "final_location" in df.columns:
            df["final_location"] = df["final_location"].astype(str).str.lower().str.strip()

        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

        sold_cols = [c for c in df.columns if "sold" in c and "igr" in c]
        if "demand" not in df.columns:
            df["demand"] = df[sold_cols].sum(axis=1) if sold_cols else 0

        _cached_df = df
        return df
    except Exception as e:
        logging.error(f"Failed to load Excel: {e}")
        return None

@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_file(request):
    global _cached_df
    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        return Response({"error": "No file provided."}, status=400)

    if not uploaded_file.name.endswith(('.xlsx', '.xls')):
        return Response({"error": "Invalid file format."}, status=400)

    try:
        df = pd.read_excel(uploaded_file)
        df.columns = (
            df.columns.astype(str).str.strip().str.lower()
            .str.replace(" ", "_").str.replace("-", "_")
        )

        if "final_location" in df.columns:
            df["final_location"] = df["final_location"].astype(str).str.lower().str.strip()

        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

        sold_cols = [c for c in df.columns if "sold" in c and "igr" in c]
        if "demand" not in df.columns:
            df["demand"] = df[sold_cols].sum(axis=1) if sold_cols else 0

        _cached_df = df
        load_dataframe.cache_clear()
        return Response({"message": "File uploaded successfully."})
    except Exception:
        return Response({"error": "Failed to process file."}, status=500)

@api_view(["POST"])
def analyze(request):
    df = load_dataframe()
    if df is None:
        return Response({"summary": "No data available."}, status=500)

    query = (request.data.get("area") or "").lower().strip()
    if not query:
        return Response({"summary": "Missing query."}, status=400)

    locations = df["final_location"].dropna().unique().tolist()
    price_cols = detect_price_cols(df)

    m = re.search(r"last\s+(\d+)\s+years", query)
    last_n = int(m.group(1)) if m else None

    found_locs = [
        loc for loc in locations
        if loc in query or fuzzy_match_location(query, [loc])
    ]

    if not found_locs:
        return Response({"summary": f"No matching location found for '{query}'."}, status=400)

    # Detect query type
    if "compare" in query and "demand" in query:
        query_type = "demand_trends"
    elif "price growth" in query:
        query_type = "price_growth"
    else:
        query_type = "analysis"

    table_data, summaries = [], []
    year_map = {}   # ⭐ KEY FIX – MERGE ROWS PER YEAR

    for loc in found_locs:
        area = df[df["final_location"] == loc].copy()
        if last_n:
            max_year = int(area["year"].max())
            area = area[area["year"] > max_year - last_n]

        area = area.sort_values("year")

        # Summary
        summaries.append({
            "location": loc.title(),
            "mockSummary": generate_mock_summary(area, price_cols, loc, last_n),
        })

        # MERGE ALL LOCATIONS INTO SINGLE YEAR ROWS
        for year, group in area.groupby("year"):
            year = int(year)

            if year not in year_map:
                year_map[year] = {"year": year}

            # Demand
            if query_type in ["analysis", "demand_trends"]:
                year_map[year][loc.title()] = int(group["demand"].sum())

            # Price
            if query_type in ["analysis", "price_growth"]:
                avg_price = (
                    group[price_cols]
                    .apply(lambda x: pd.to_numeric(x, errors="coerce"))
                    .mean().mean()
                )
                year_map[year][f"{loc.title()}_price"] = round(avg_price, 2)

        # Table data
        cols = ["final_location", "year"]
        if query_type in ["analysis", "demand_trends"]:
            cols.append("demand")
        if query_type in ["analysis", "price_growth"]:
            cols += price_cols

        table_data.extend(area[cols].to_dict(orient="records"))

    # Convert merged years to sorted list
    chart_data = list(sorted(year_map.values(), key=lambda x: x["year"]))

    return Response({
        "summary": summaries,
        "chartData": chart_data,
        "tableData": table_data
    })
