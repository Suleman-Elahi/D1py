# D1py
A very simple wrapper for Cloudflare D1 Databases' REST API

## Installtion

`git clone https://github.com/Suleman-Elahi/D1py`

`cd D1py && pip install .`

For now just install like this...in future maybe uploaded to pypi if needed.

## Included Functions:
`list_db()`                                   --> List down all databses from your account. Returns an array with the database name and ids. Use it to get db_id for further interaction.

`create_db(db_name)`                          --> Create a D1 databse in your Cloudflare account.

`delete_db(database_id)`                      --> Deletes a D1 databse from your Cloudflare account.

`get_db(database_id)`                         --> Get a specific D1 database from your Cloudflare account.

`query_db(database_id, sql, params=None)`     --> Run a SQL query against a D1 database in your account.

`raw_db_query(db_id, sql, params=None)`       --> Run a raw SQL query against a D1 database in your account.

## Usage:

```
from D1py import D1py

d1 = D1py(account_id, api_token)

databases = d1.list_db()

print(databases)
```

## More Examples:

`print(d1.query_db(database_id, "select ids from t1;"))`

`print(d1.query_db(database_id,
                  "insert into table(field1, field2) values(?,?);",
                   params=["456", "hey john"])
                   )`

Better save the `database_id` as an environment variable and use.

A typical response looks like this:

```
{
  'result': [
    {
      'results': [
        
      ],
      'success': True,
      'meta': {
        'served_by': 'v3-prod',
        'duration': 0.2481,
        'changes': 1,
        'last_row_id': 2,
        'changed_db': True,
        'size_after': 20480,
        'rows_read': 0,
        'rows_written': 2
      }
    }
  ],
  'success': True,
  'errors': [
    
  ]
}
```
Or with errors:

```
{
  'result': [
    
  ],
  'success': False,
  'errors': [
    {
      'code': 7500,
      'message': 'no such column: ids at offset 7'
    }
  ]
}
```
After running each request, you can check the status if `success` variable to check if the call was successful.

Learn more about Cloudflare's D1 Database' REST API: https://developers.cloudflare.com/api/operations/cloudflare-d1-list-databases

