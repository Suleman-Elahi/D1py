from D1py import D1py

account_id = "3c424e10f2e1b69424c8d5cfb1f039a2"
api_token = "R-8SMN2oHEMu1Bo6m2PCzduetn4Hng_DBO2sY8Wu"

d1 = D1py(account_id, api_token)

# List databases
#print(d1.query_db("d5846699-c548-445f-94f6-c77af91af700", "select ids from t1;"))

print(d1.query_db("d5846699-c548-445f-94f6-c77af91af700",
                  "insert into t1(id, c) values(?,?);",
                   params=["456", "hey john"])
                   )
