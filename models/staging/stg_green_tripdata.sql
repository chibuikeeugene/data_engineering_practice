{{ config(materialized='view') }}

select * from trips_data_all.yellow_table