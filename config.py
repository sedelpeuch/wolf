token = ""
url = "https://gestion.eirlab.net/api/index.php/"
headers = {"Accept": "application/json", "DOLAPIKEY": token}
url_member = "members?sortfield=t.rowid&sortorder=ASC&limit=600"
url_user = "users?sortfield=t.rowid&sortorder=ASC&limit=100"
url_product = "products?sortfield=t.ref&sortorder=ASC&limit=1000&includestockdata=1"
url_warehouse = "warehouses?sortfield=t.rowid&sortorder=ASC&limit=20"
url_agenda = "agendaevents?sortfield=t.id&sortorder=ASC&limit=1000"
url_thirdparty_supplier = "thirdparties?sortfield=t.rowid&sortorder=ASC&limit=1000&mode=4"
url_supplierorder_draft = "supplierorders?sortfield=t.rowid&sortorder=ASC&limit=1000&status=draft"
IP_PUBLIC_WOLF = '192.168.0.117'
