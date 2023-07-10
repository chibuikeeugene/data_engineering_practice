/*update the default materialized property to table*/
{{ config(materialized='view') }}

select * from  {{source('staging', 'yellow_taxi')}} limit 100