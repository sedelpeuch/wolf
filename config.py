token = ""
url = "https://gestion.eirlab.net/api/index.php/"
headers = {"Accept": "application/json", "DOLAPIKEY": token}
url_member = "members?sortfield=t.rowid&sortorder=ASC&limit=600"
url_user = "users?sortfield=t.rowid&sortorder=ASC&limit=100"
url_product = "products?sortfield=t.ref&sortorder=ASC&limit=600"
url_warehouse = "warehouses?sortfield=t.rowid&sortorder=ASC&limit=20"
