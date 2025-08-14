#!/usr/bin/env python3
"""
Catalog Analysis Script
Analyzes the structure of your catalog Excel files to help with enrichment setup.
"""
import pandas as pd
import os
from pathlib import Path

def analyze_excel_file(file_path: str) -> dict:
    """Analyze an Excel file and return its structure information."""
    try:
        # Read the Excel file
        df = pd.read_excel(file_path, sheet_name=0)
        
        analysis = {
            "file_name": os.path.basename(file_path),
            "file_size_mb": round(os.path.getsize(file_path) / (1024 * 1024), 2),
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": list(df.columns),
            "sample_data": {},
            "data_types": {},
            "missing_values": {},
            "unique_values": {}
        }
        
        # Analyze each column
        for column in df.columns:
            # Sample data (first non-null value)
            sample_value = df[column].dropna().iloc[0] if not df[column].dropna().empty else None
            analysis["sample_data"][column] = str(sample_value)[:100] if sample_value else None
            
            # Data types
            analysis["data_types"][column] = str(df[column].dtype)
            
            # Missing values
            missing_count = df[column].isna().sum()
            analysis["missing_values"][column] = {
                "count": int(missing_count),
                "percentage": round((missing_count / len(df)) * 100, 2)
            }
            
            # Unique values (for categorical columns)
            unique_count = df[column].nunique()
            analysis["unique_values"][column] = {
                "count": int(unique_count),
                "percentage": round((unique_count / len(df)) * 100, 2)
            }
        
        return analysis
        
    except Exception as e:
        return {
            "file_name": os.path.basename(file_path),
            "error": str(e)
        }

def main():
    """Main analysis function."""
    print("🔍 Catalog File Analysis")
    print("=" * 50)
    
    # Look for catalog examples in the app directory
    catalog_dir = Path("app/catalog_examples")
    
    if not catalog_dir.exists():
        print("❌ Catalog examples directory not found!")
        print("Expected location: app/catalog_examples/")
        return
    
    excel_files = list(catalog_dir.glob("*.xlsx")) + list(catalog_dir.glob("*.xls"))
    
    if not excel_files:
        print("❌ No Excel files found in catalog examples directory!")
        return
    
    print(f"📁 Found {len(excel_files)} Excel files to analyze:")
    print()
    
    for file_path in excel_files:
        print(f"📊 Analyzing: {file_path.name}")
        print("-" * 40)
        
        analysis = analyze_excel_file(str(file_path))
        
        if "error" in analysis:
            print(f"❌ Error: {analysis['error']}")
            print()
            continue
        
        print(f"📏 File Size: {analysis['file_size_mb']} MB")
        print(f"📊 Total Rows: {analysis['total_rows']:,}")
        print(f"📋 Total Columns: {analysis['total_columns']}")
        print()
        
        print("📋 Column Analysis:")
        for column in analysis["columns"]:
            print(f"  • {column}")
            print(f"    - Type: {analysis['data_types'][column]}")
            print(f"    - Missing: {analysis['missing_values'][column]['count']} ({analysis['missing_values'][column]['percentage']}%)")
            print(f"    - Unique: {analysis['unique_values'][column]['count']} ({analysis['unique_values'][column]['percentage']}%)")
            
            sample = analysis['sample_data'][column]
            if sample:
                print(f"    - Sample: {sample}")
            print()
        
        print("=" * 50)
        print()
    
    print("💡 Recommendations for Enrichment:")
    print("1. Identify key fields for product identification (name, SKU, UPC)")
    print("2. Check for consistent data formats across files")
    print("3. Note any missing or inconsistent data that might affect enrichment")
    print("4. Consider standardizing column names for better processing")

if __name__ == "__main__":
    main()

