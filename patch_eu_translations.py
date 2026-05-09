#!/usr/bin/env python3
"""
Adds eu_ES translations directly into ir_model_fields.field_description
for fields that are missing Basque translations.
Runs inside the Odoo container.
"""
import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['--config=/etc/odoo/odoo.conf'])

# Maps English source text → Basque translation
# Covers base Odoo fields visible in the OpenEduCat views
EU_TRANSLATIONS = {
    # Core field labels
    "Name": "Izena",
    "Email": "Helbide elektronikoa",
    "Phone": "Telefonoa",
    "Mobile": "Mugikorra",
    "Phone/Mobile": "Tel./Mugikorra",
    "Active": "Aktiboa",
    "Code": "Kodea",
    "Date": "Data",
    "State": "Egoera",
    "Status": "Egoera",
    "Title": "Titulua",
    "Type": "Mota",
    "Notes": "Oharrak",
    "Reference": "Erreferentzia",
    "Language": "Hizkuntza",
    "Timezone": "Ordu Eremua",
    "Timezone offset": "Ordu Eremua Aldaketa",
    "Image": "Irudia",
    "Image 128": "Irudia 128",
    "Image 256": "Irudia 256",
    "Image 512": "Irudia 512",
    "Image 1024": "Irudia 1024",
    "Avatar": "Avatarra",
    "Avatar 128": "Avatarra 128",
    "Avatar 256": "Avatarra 256",
    "Avatar 512": "Avatarra 512",
    "Avatar 1024": "Avatarra 1024",
    "Barcode": "Barra Kodea",
    "Color Index": "Kolore Indizea",
    "Tags": "Etiketak",
    "Categories": "Kategoriak",
    "Category": "Kategoria",
    # Address fields
    "Street": "Kalea",
    "Street2": "Kalea 2",
    "City": "Hiria",
    "Zip": "Posta Kodea",
    "ZIP": "Posta Kodea",
    "Country": "Herrialdea",
    "Country Code": "Herrialde Kodea",
    "Complete Address": "Helbide Osoa",
    "Inlined Complete Address": "Helbide Osoa (lerro bakarrean)",
    "Address Type": "Helbide Mota",
    "Additional info": "Informazio gehigarria",
    "Geo Latitude": "Latitude",
    "Geo Longitude": "Longitudea",
    # Company/partner fields
    "Company": "Enpresa",
    "Company Name": "Enpresa Izena",
    "Company Type": "Enpresa Mota",
    "Company Name Entity": "Enpresa Entitate Izena",
    "Company database ID": "Enpresa BD ID",
    "Company ID": "Enpresa ID",
    "Commercial Entity": "Entitate Komertziala",
    "Is a Company": "Enpresa da",
    "Related Company": "Enpresa Erlazionatua",
    "Companies that refers to partner": "Kontaktua aipatzen duten enpresak",
    "Parent name": "Gurasoaren izena",
    "Complete Name": "Izen Osoa",
    "Display Name": "Bistaratzeko Izena",
    "Normalized Email": "Helbide Elektroniko Normalizatua",
    "Formatted Email": "Helbide Elektroniko Formateatua",
    "Sanitized Number": "Zenbaki Garbitu",
    "Format": "Formatua",
    # Contact fields
    "Contact": "Kontaktua",
    "Job Position": "Lan Posizioa",
    "Industry": "Industria",
    "Website": "Webgunea",
    "Website URL": "Webguneen URL",
    "Website Link": "Webgunearen Esteka",
    "Signature": "Sinadura",
    "Tax ID": "IFZ",
    "Fiscal Position": "Zerga Posizioa",
    "Fiscal Country Codes": "Zerga Herrialde Kodeak",
    "Bank": "Bankua",
    "Banks": "Bankuak",
    "Pricelist": "Prezioen Zerrenda",
    "Currency": "Moneta",
    "Customer Payment Terms": "Bezeroaren Ordainketa Baldintzak",
    "Vendor Payment Terms": "Hornitzailearen Ordainketa Baldintzak",
    "Customer Rank": "Bezero Maila",
    "Supplier Rank": "Hornitzaile Maila",
    "Supplier Currency": "Hornitzailearen Moneta",
    "Buyer": "Eroslea",
    "Salesperson": "Saltzailea",
    "Credit Limit": "Kreditu Muga",
    "Payable Limit": "Ordaintzeko Muga",
    "Partner Limit": "Bazkide Muga",
    "Show Credit Limit": "Erakutsi Kreditu Muga",
    "Credit To Invoice": "Fakturatu Gabeko Kreditua",
    "Total Invoiced": "Fakturatutako Guztira",
    "Total Payable": "Ordaintzeko Guztira",
    "Total Receivable": "Kobratzeko Guztira",
    "# Vendor Bills": "Hornitzaile Fakturak",
    "Account Payable": "Ordaintzeko Kontua",
    "Account Receivable": "Kobratzeko Kontua",
    "Has Unreconciled Entries": "Kontziliatu Gabeko Sarrerak",
    "Latest Invoices & Payments Matching Date": "Azken Faktura eta Ordainketen Bat-etortze Data",
    "Days Sales Outstanding (DSO)": "Salmenta Kobratzeko Egunak",
    "Purchase Order Count": "Erosketa Aginduen Kopurua",
    "Purchase Order Warning": "Erosketa Aginduen Oharra",
    "Journal Items": "Kontabilitate Sarrerak",
    "Intra-Community Valid": "EE Barne Balioduna",
    "Perform Vies Validation": "VIES Egiaztapena Egin",
    "Vies Vat To Check": "VIES BEZ Egiaztatzeko",
    "Duplicated Bank Account Partners Count": "Kontu Bikoiztuen Kopurua",
    "Partner Contracts": "Bazkidearen Kontratuak",
    "Partner with same Company Registry": "Erregistro Berdineko Bazkidea",
    "Partner with same Tax ID": "IFZ Berdineko Bazkidea",
    "Payment Token Count": "Ordainketa Token Kopurua",
    "Payment Tokens": "Ordainketa Tokenak",
    "Peppol e-address (EAS)": "Peppol helbide elektronikoa (EAS)",
    "Peppol Endpoint": "Peppol Puntua",
    "Hide Peppol Fields": "Ezkutatu Peppol Eremuak",
    "Message for Invoice": "Fakturarako Mezua",
    "Message for Purchase Order": "Erosketa Agindurako Mezua",
    "GLN": "GLN",
    "Global Location Number": "Kokaleku Zenbaki Orokorra",
    "Physical GLN": "Kokaleku Fisikoa GLN",
    "Logical Operational Point": "Puntu Operazional Logikoa",
    # User/access fields
    "Related User": "Erlazionatutako Erabiltzailea",
    "Users": "Erabiltzaileak",
    "User": "Erabiltzailea",
    "Login": "Saioa Hasi",
    "Signup Token": "Erregistro Tokena",
    "Signup Token Type": "Erregistro Token Mota",
    "Signup Expiration": "Erregistro Iraungipena",
    "Signup Token is Valid": "Erregistro Tokena Balioduna da",
    "Signup URL": "Erregistro URLa",
    "Share Partner": "Partekatu Bazkidea",
    "Can Publish": "Argitaratu dezake",
    "Is Public": "Publikoa da",
    "Is Published": "Argitaratuta dago",
    "Visible on current website": "Egungo webgunean ikusgai",
    "Website Messages": "Webgunearen Mezuak",
    "Latest Connection": "Azken Konexioa",
    "Blacklist": "Zerrenda Beltza",
    "Blacklisted Phone Is Mobile": "Mugikorra Zerrenda Beltzean",
    "Blacklisted Phone is Phone": "Telefonoa Zerrenda Beltzean",
    "Phone Blacklisted": "Telefonoa Blokeatuta",
    "Bounce": "Itzulera",
    # Messaging/chatter fields
    "Messages": "Mezuak",
    "Followers": "Jarraitzaileak",
    "Followers (Partners)": "Jarraitzaileak (Bazkideak)",
    "Is Follower": "Jarraitzailea da",
    "Has Message": "Mezua du",
    "Message Delivery error": "Mezu Bidaltzeko Errorea",
    "SMS Delivery error": "SMS Bidaltzeko Errorea",
    "Number of errors": "Errore kopurua",
    "Number of Actions": "Ekintza kopurua",
    "Number of messages requiring action": "Ekintza behar duten mezu kopurua",
    "Number of messages with delivery error": "Bidaltzeko errorea duten mezu kopurua",
    "Action Needed": "Ekintza Beharrezkoa",
    "Starred Message": "Mezu Nabarmendua",
    "Attachment Count": "Eranskin kopurua",
    "Website communication history": "Webgunearen komunikazio historia",
    "Channels": "Kanalak",
    # Activity fields
    "Activities": "Jarduerak",
    "Activity": "Jarduera",
    "Activity State": "Jarduera Egoera",
    "Activity Exception Decoration": "Jarduera Salbuespen Apaingarria",
    "Activity Type Icon": "Jarduera Mota Ikonoa",
    "My Activity Deadline": "Nire Jardueraren Epemuga",
    "Next Activity Deadline": "Hurrengo Jardueraren Epemuga",
    "Next Activity Summary": "Hurrengo Jardueraren Laburpena",
    "Next Activity Type": "Hurrengo Jarduera Mota",
    "Icon": "Ikonoa",
    "Active Lang Count": "Hizkuntza Aktibo Kopurua",
    # Employee fields
    "Employee": "Langilea",
    "Employees": "Langileak",
    "Employees Count": "Langile Kopurua",
    "HR Employee": "Giza Baliabideak - Langilea",
    "Responsible User": "Arduradun Erabiltzailea",
    # OpenEduCat specific
    "Fees Term": "Tasen Epea",
    "Fees Collection Details": "Tasen Bilketa Xehetasunak",
    "Fees Details Count": "Tasen Xehetasun Kopurua",
    "Asset": "Aktibo",
    "Self": "Bera",
    "Visitor": "Bisitaria",
    "Visitors": "Bisitariak",
    "Roles": "Rolak",
    "Session Count": "Saio Kopurua",
    "Sessions": "Saioak",
    "Venue": "Lekua",
    "Library Card": "Liburutegi Txartela",
    "Movements": "Mugimendua",
    "Media Movement Lines Count": "Multimedia Mugimendu Lerro Kopurua",
    "Assignment Count": "Lan Kopurua",
    "Assignment(s)": "Lan(ak)",
    "Minimum Unit Load": "Gutxieneko Karga",
    "Receipt Reminder": "Jasotzeko Oroigarri",
    "Days Before Receipt": "Jasotzea Baino Egun Lehenago",
    "Facturae EDI Residency Type Code": "Facturae EDI Egoitza Mota Kodea",
}

with odoo.registry('kudeaketa').cursor() as cr:
    updated = 0
    skipped = 0

    # Get all field_description entries missing eu_ES
    cr.execute("""
        SELECT id, field_description
        FROM ir_model_fields
        WHERE field_description IS NOT NULL
          AND field_description::text NOT LIKE '%%eu_ES%%'
    """)
    rows = cr.fetchall()
    print(f"Fields without eu_ES: {len(rows)}")

    for field_id, desc in rows:
        import json
        try:
            data = json.loads(desc) if isinstance(desc, str) else desc
        except Exception:
            skipped += 1
            continue

        en_val = data.get('en_US', '')
        translation = EU_TRANSLATIONS.get(en_val)

        if not translation:
            # Try stripping trailing colon (e.g. "Created by:" → "Created by")
            translation = EU_TRANSLATIONS.get(en_val.rstrip(':').strip())

        if translation:
            data['eu_ES'] = translation
            cr.execute(
                "UPDATE ir_model_fields SET field_description = %s WHERE id = %s",
                (json.dumps(data), field_id)
            )
            updated += 1
        else:
            skipped += 1

    cr.commit()
    print(f"Updated {updated} fields, skipped {skipped}")
