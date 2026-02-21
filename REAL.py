import nflreadpy as nfl
import polars as pl
import random
# import ageFactor   # uncomment when your age function is ready


# -----------------------------------
# Projection multiplier function
# -----------------------------------
def projection_multiplier(position, age):
    position = position.upper()

    # Base age adjustment
    if position == "QB":
        factor = 1.0 - max(0, (age - 30) * 0.03)
    elif position == "RB":
        factor = 1.0 - max(0, (age - 27) * 0.05)
    elif position == "WR":
        factor = 1.0 - max(0, (age - 28) * 0.04)
    elif position == "TE":
        factor = 1.0 - max(0, (age - 28) * 0.03)
    else:
        raise ValueError(f"Unknown position: {position}")

    # Rising star boost
    if position == "QB" and age <= 25:
        factor *= 1.08
    elif position == "RB" and age <= 23:
        factor *= 1.10
    elif position == "WR" and age <= 23:
        factor *= 1.10
    elif position == "TE" and age <= 24:
        factor *= 1.05

    return factor


# -----------------------------------
# Group players so each appears once
# -----------------------------------
def group_and_aggregate(df):
    return (
        df.group_by(['player_id', 'player_name', 'position'])
        .agg([
            pl.col('fantasy_points').sum().alias('fantasy_points'),
            pl.col('passing_yards').sum().alias('passing_yards'),
            pl.col('passing_tds').sum().alias('passing_tds'),
            pl.col('rushing_yards').sum().alias('rushing_yards'),
            pl.col('rushing_tds').sum().alias('rushing_tds'),
            pl.col('receiving_yards').sum().alias('receiving_yards'),
            pl.col('receiving_tds').sum().alias('receiving_tds'),
        ])
    )


# -----------------------------------
# Add projected points column
# -----------------------------------
def add_projected_points(df):
    return df.with_columns(
        (
            pl.col("fantasy_points") *
            pl.struct(["position", "player_name"]).map_elements(
                lambda x: projection_multiplier(
                    x["position"],
                    random.uniform(20, 40)  # replace with ageFactor.ageFactor(x["player_name"])
                ),
                return_dtype=pl.Float64,
            )
        ).round(2).alias("projected_points")
    )


# -----------------------------------
# Load data
# -----------------------------------
stats = nfl.load_player_stats(2024)

# Replace NaN with 0
stats = stats.fill_nan(0)


# -----------------------------------
# Create position tables
# -----------------------------------
qb_df = stats.filter(pl.col('position') == 'QB')
rb_df = stats.filter(pl.col('position') == 'RB')
wr_df = stats.filter(pl.col('position') == 'WR')
te_df = stats.filter(pl.col('position') == 'TE')


# -----------------------------------
# Aggregate
# -----------------------------------
qb_df = group_and_aggregate(qb_df)
rb_df = group_and_aggregate(rb_df)
wr_df = group_and_aggregate(wr_df)
te_df = group_and_aggregate(te_df)


# -----------------------------------
# Add projections
# -----------------------------------
qb_df = add_projected_points(qb_df)
rb_df = add_projected_points(rb_df)
wr_df = add_projected_points(wr_df)
te_df = add_projected_points(te_df)


# -----------------------------------
# Sort and rank
# -----------------------------------
qb_df = qb_df.sort('projected_points', descending=True)
rb_df = rb_df.sort('projected_points', descending=True)
wr_df = wr_df.sort('projected_points', descending=True)
te_df = te_df.sort('projected_points', descending=True)

# -----------------------------------
# Show results
# -----------------------------------
print("\nTop 10 QBs:")
print(qb_df.head(10))

print("\nTop 10 RBs:")
print(rb_df.head(10))

print("\nTop 10 WRs:")
print(wr_df.head(10))

print("\nTop 10 TEs:")
print(te_df.head(10))