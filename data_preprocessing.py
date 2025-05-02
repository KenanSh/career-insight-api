import pandas as pd
from datetime import datetime

# Change settings in order to show all columns in printout
# pd.set_option('display.max_columns', None)
# pd.set_option('display.width', 200)

# Declaring Pathes
SOURCE_DATASET = 'data\source\Data_BusinessCase.xls'
OUTPUT_DATASET = "data\processed\processed_data.xlsx"


# Loading all sheets as a dictionary where (keys are sheets) and (values are DataFrames of the content)
sheets = pd.read_excel(SOURCE_DATASET, sheet_name=None)
print("Loaded Sheets:", list(sheets.keys()))

# Preview first rows of each sheet 
for sheet_name, df in sheets.items():
    print(f"Sheet: {sheet_name}")
    print(df.head())


# Data Cleaning
# 1. Inspecting missing values in important sheets columns
profiles = sheets['profiles_rows']
positions = sheets['positions_rows']
profile_cols = ['id', 'full_name', 'headline']
position_cols = ['profile_id', 'company_name', 'title', 'start_year', 'start_month', 'end_year', 'end_month']

# Count missings in profiles
print("Missing values in 'profiles_rows':")
print(profiles[profile_cols].isnull().sum())

# Count missings in positions
print("Missing values in 'positions_rows':")
print(positions[position_cols].isnull().sum())

# total number
print(f"Total profiles: {len(profiles)}")
print(f"Total positions: {len(positions)}")

# Select relevant columns for more clear view
cols = ['id', 'profile_id', 'title', 'start_month', 'start_year', 'end_month', 'end_year']
positions_view = positions[cols].copy()

# Sort by profile_id, start_year, then start_month (ascending)
positions_view.sort_values(by=['profile_id', 'start_year', 'start_month'], inplace=True)
positions_view.reset_index(drop=True, inplace=True)
print(positions_view)

# Group by profile_id and summarize missing values
missing_summary = (
    positions_view
    .groupby('profile_id')
    .agg(
        total_positions=('start_month', 'count'),
        missing_start_month=('start_month', lambda x: x.isna().sum()),
        missing_end_month=('end_month', lambda x: x.isna().sum()),
        missing_end_year=('end_year', lambda x: x.isna().sum())
    )
    .reset_index()
)

# Filter to show only profiles with at least one missing field
missing_summary = missing_summary[
    (missing_summary['missing_start_month'] > 0) |
    (missing_summary['missing_end_month'] > 0) |
    (missing_summary['missing_end_year'] > 0)
]

# Display the summary
print("Missing Values Summary per Profile:")
print(missing_summary)


########################################################################################################


# 2. Handling missing values (filling them in logic mentioned in README file)
# Get current date
current_year = datetime.today().year
current_month = datetime.today().month

# For final cleaned data
filled_positions = []

# Loop through each profile's positions
for profile_id, group in positions_view.groupby('profile_id'):
    group = group.copy().reset_index(drop=True)

    for i in range(len(group)):
        # Fill missing 'start_month'
        if pd.isna(group.loc[i, 'start_month']):
            if i == 0:
                group.loc[i, 'start_month'] = 1  # First job, assume January
            else:
                prev_end_month = group.loc[i - 1, 'end_month']
                prev_end_year = group.loc[i - 1, 'end_year']
                current_start_year = group.loc[i, 'start_year']

                if pd.notna(prev_end_month) and pd.notna(prev_end_year) and pd.notna(current_start_year):
                    if prev_end_month == 12 and prev_end_year != current_start_year:
                        group.loc[i, 'start_month'] = 1
                    else:
                        group.loc[i, 'start_month'] = prev_end_month
                else:
                    group.loc[i, 'start_month'] = 1 

        # Fill missing 'end_year'
        if pd.isna(group.loc[i, 'end_year']):
            if i == len(group) - 1:
                group.loc[i, 'end_year'] = current_year
            else:
                next_start_year = group.loc[i + 1, 'start_year']
                group.loc[i, 'end_year'] = next_start_year if pd.notna(next_start_year) else current_year

        # Fill missing 'end_month'
        if pd.isna(group.loc[i, 'end_month']):
            if i == len(group) - 1:
                group.loc[i, 'end_month'] = current_month
            else:
                next_start_month = group.loc[i + 1, 'start_month']
                next_start_year = group.loc[i + 1, 'start_year']
                current_end_year = group.loc[i, 'end_year']

                if pd.notna(next_start_month) and pd.notna(next_start_year) and pd.notna(current_end_year):
                    if next_start_month == 1 and next_start_year == current_end_year + 1:
                        group.loc[i, 'end_month'] = 12
                    elif current_end_year == next_start_year and next_start_month > 1:
                        group.loc[i, 'end_month'] = next_start_month - 1
                    else:
                        group.loc[i, 'end_month'] = next_start_month
                else:
                    group.loc[i, 'end_month'] = current_month

    filled_positions.append(group)

# Combine and preview the result
positions_filled = pd.concat(filled_positions, ignore_index=True)
print(positions_filled[['id', 'profile_id', 'title', 'start_month', 'start_year', 'end_month', 'end_year']])

# Update positions from positions_filled using 'id' as key
if 'id' in positions.columns and 'id' in positions_filled.columns:
    positions.set_index('id', inplace=True)
    positions_filled.set_index('id', inplace=True)

    # Update relevant columns from cleaned data
    positions.update(positions_filled[['start_month', 'start_year', 'end_month', 'end_year']])

    # Restore index as column
    positions.reset_index(inplace=True)
    positions_filled.reset_index(inplace=True)

# Recheck for any remaining missing values
print("Rechecking for missing values in updated 'positions':")
print(positions[position_cols].isnull().sum())

# Print final counts
print(f"Total profiles: {len(profiles)}")
print(f"Total cleaned positions: {len(positions)}")


########################################################################################################


# 3. For bigger data where there might be a redundant data
# positions.drop_duplicates(inplace=True)
# print(positions)


########################################################################################################


# 4. Drop columns that won't serve our mission
# List of columns to drop
irrelevant_columns = [
    'company_logo',
    'company_url',
    'location',
    'created_at',
    'updated_at'
]

# Drop only if they exist (to avoid KeyError)
positions.drop(columns=[col for col in irrelevant_columns if col in positions.columns], inplace=True)
print("Cleaned `positions` columns:")
print(positions.columns.tolist())


########################################################################################################


# Save the processed data (only two sheets)
# Select relevant/cleaned columns from positions
positions_cleaned = positions.copy()
with pd.ExcelWriter(OUTPUT_DATASET, engine='openpyxl') as writer:
    profiles.to_excel(writer, sheet_name='profiles', index=False)
    positions_cleaned.to_excel(writer, sheet_name='positions', index=False)
print(f"Cleaned data exported to: {OUTPUT_DATASET}")


########################################################################################################


# Constant data (infered from little search online)
COMPANY_CATEGORY_MAP = {
    "Pfizer": "Big Pharma",
    "Roche": "Big Pharma",
    "Novartis": "Big Pharma",
    "Astrazeneca": "Big Pharma",
    "Sanofi": "Mid Pharma",
    "GSK": "Mid Pharma",
    "Moderna": "Biotech",
    "Bayer": "Other"
}

profiles = pd.read_excel(OUTPUT_DATASET, sheet_name="profiles")
positions = pd.read_excel(OUTPUT_DATASET, sheet_name="positions")

# Normalize company names and categorize
positions['company_name'] = positions['company_name'].str.strip().str.title()
positions['company_category'] = positions['company_name'].map(COMPANY_CATEGORY_MAP).fillna("Other")

# Edit columns by combining start/end month/year together for each position for calculations (day is default for 1)
positions['start_date'] = pd.to_datetime(
    positions[['start_year', 'start_month']].assign(day=1).astype(str).agg('-'.join, axis=1),
    errors='coerce'
)
positions['end_date'] = pd.to_datetime(
    positions[['end_year', 'end_month']].assign(day=1).astype(str).agg('-'.join, axis=1),
    errors='coerce'
)
positions['duration(days)'] = (positions['end_date'] - positions['start_date']).dt.days
positions.drop(columns=['start_month', 'start_year', 'end_month', 'end_year'], inplace=True)

# Save to new Excel file with both sheets
with pd.ExcelWriter(OUTPUT_DATASET, engine='openpyxl') as writer:
    profiles.to_excel(writer, sheet_name='profiles', index=False)
    positions.to_excel(writer, sheet_name='positions', index=False)
print(f"Updated data exported to: {OUTPUT_DATASET}")