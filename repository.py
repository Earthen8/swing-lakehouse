from dagster import repository, load_assets_from_modules, ScheduleDefinition, define_asset_job
from ingestion import assets as bronze_silver_layer
from transformation import assets as gold_layer

run_all_job = define_asset_job(name="update_market_data", selection="*")

daily_schedule = ScheduleDefinition(
    job=run_all_job,
    cron_schedule="15 9 * * 1-5", 
    execution_timezone="UTC"
)

@repository
def my_repository():
    return [
        load_assets_from_modules([bronze_silver_layer]),
        load_assets_from_modules([gold_layer]),
        daily_schedule,
    ]
