{{ config(materialized='view') }}

select * from  {{source('staging', 'yellow_table')}} limit 100