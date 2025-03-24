# History Directory
In this table we store all the performances of each MATCH event for statistical purposes and long term analysis.

Considering the current ER diagram, the report query is the following: 
```sql
select 
	date, 
	count(jp.id) num_joined_players, 
	count(distinct jp.table_id) num_tables, 
	count(distinct jp.user_id) num_distinct_users
from 
	joined_players jp
	join table_propositions tp on (jp.table_id = tp.id)
group by "date" 
order by "date"

```

The query needs to be run after each event and the corresponding record (or records if it's a multi-date event) need to be added into the corresponding csv file.

For example for MATCH, use the `static/history/match_report.csv`