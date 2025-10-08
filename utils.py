
##################################################################
#  Utility functions to interact with the EU pesticide database  #
#                   and for the pipeline                         #
##################################################################

#######################   Imports  ###############################

import httpx
import pandas as pd
from pathlib import Path
import base64
import fitz  # PyMuPDF

##################   URLS & Constants   ##########################

BASE_URL_PRODUCT = "https://api.datalake.sante.service.ec.europa.eu/sante/pesticides/pesticide_residues_products"
BASE_URL_PEST =  "https://api.datalake.sante.service.ec.europa.eu/sante/pesticides/active_substances"
BASE_URL_PCR= "https://api.datalake.sante.service.ec.europa.eu/sante/pesticides/product-current-mrl-all-residues"
BASE_URL_MRL =  "https://api.datalake.sante.service.ec.europa.eu/sante/pesticides/pesticide_residues_mrls"
HEADERS = {"Content-Type": "application/json","Cache-Control": "no-cache"}
PARAMS = {"format": "json", "api-version": "v2.0","language":"en"}
PARAMS_PEST = {"format": "json", "api-version": "v2.0"}
BASE_DIR = Path(__file__).resolve().parent  # Directory of the current script
EXAMPLES_PATH = BASE_DIR / "examples" 
JSON_PATH = BASE_DIR / "json_outputs" 

##################   Functions   ####################################


def fetch_all_data(url, params, timeout=30.0) -> list[dict]:
    """ Function to retrieve the data for different EU API endpoint"""
    
    all_items: list[dict] = []
    
    with httpx.Client(timeout=timeout) as client:
        
        resp = client.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        payload = resp.json()
        all_items.extend(payload.get("value", []))
        next_link = payload.get("nextLink")
        
        while next_link:
            resp = client.get(next_link, headers=HEADERS) 
            resp.raise_for_status()
            payload = resp.json()
            all_items.extend(payload.get("value", []))
            next_link = payload.get("nextLink")
    
    return all_items


def get_substance_mrl_EU(product_id : str, substance_id : str):
    """ 
    Allow to retrieve the MLR for a couple (product id / substance id)
    Will return the MLR data applicable if it exists in the EU database
    
    Inputs :
    
    - product_id (str) : the id of the product in the EU database
    - substance_id (str) : the id of the substance in the EU database
    
    """

    params = PARAMS_PEST | {"pesticide_residue_id":substance_id, "product_id":product_id}
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(BASE_URL_MRL, headers=HEADERS, params=params)
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get("value")
        data = [mlr for mlr in data if mlr.get("applicability_text") == "Applicable"]
        return data


def create_and_dump_data():
    """ Function to dump product and pesticide data to csv files"""
    
    # Create a dataframe with all the products from the EU database 
    prod = fetch_all_data(url=BASE_URL_PRODUCT, params=PARAMS) 
    df_prod = pd.DataFrame(prod)
    df_prod["product_parent_id"] = df_prod["product_parent_id"].fillna(0).astype(int)
    df_prod.to_csv("eu_products.csv", index=False, sep="|")

    # Create a dataframe with all the pesticides from the EU database 
    pest = fetch_all_data(url=BASE_URL_PEST, params=PARAMS_PEST) 
    df_pest = pd.DataFrame(pest)
    df_pest.to_csv("eu_pesticides.csv", index=False, sep="|")


def pdf_to_base64_images(pdf_path: str) -> list[str]:
    """
    Convert each page of a PDF into a base64-encoded PNG image.
    Returns a list of base64 strings, one for each page.
    """
    doc = fitz.open(pdf_path)
    images = []
    
    print(f"Converting {len(doc)} page(s) in base64 images...")
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        images.append(img_base64)
        print(f"  Page {page_num + 1}/{len(doc)} done")
    
    doc.close()
    return images


def fetch_mrl_data(product_name: str, sub_name: str, mrl: int) -> dict:
    """
    Fetch MRL data for a given product and substance from the EU database.
    Returns the compliance status regarding the mrl value provided.
    """
    
    # Load product and pesticide data
    df_prod = pd.read_csv("eu_products.csv", sep="|")
    df_pest = pd.read_csv("eu_pesticides.csv", sep="|")
    
    # Find product ID
    condition_product = (df_prod.product_name.str.contains(product_name, case=False, na=False))
    prod_row = df_prod[condition_product]
    if prod_row.empty:
        return {"error": f"Product '{product_name}' not found in EU database."}
    product_id = str(prod_row.iloc[0]["product_id"])
    
    # Find substance ID 
    condition_pest = (df_pest.substance_name.str.contains(sub_name, case=False, na=False))
    pest_row = df_pest[condition_pest]
    if pest_row.empty:
        return {"error": f"Substance '{sub_name}' not found in EU database."}
    substance_id = str(pest_row.iloc[0]["substance_id"])
    
    # Fetch MRL data
    mrl_data = get_substance_mrl_EU(product_id, substance_id)
    
    if not mrl_data:
        print(f"Error : No MRL data found for product '{product_name}' and substance '{sub_name}'.")
    else:
        
        print(f"MRL data found for product '{product_name}' and substance '{sub_name}'.")
        mrl_options = mrl_data[0].get("mrl_value", [])
        try: 
            mrl_options_value = float(mrl_options.replace("*", "")) if mrl_options != "No MRL required" else 0
        except ValueError:
            print(f"Warning: Unable to convert MRL option '{mrl_options}' to float. Setting to 0.")
            mrl_options_value = 0
        
        print(f"MRL options from EU database: {mrl_options}")
        print(f"MRL value from report: {mrl}")
        mrl_conditions = (mrl_options == "No MRL required") | (float(mrl) < mrl_options_value) 
        compliance_results = "CONFORME" if mrl_conditions  else "NON CONFORME"    
        
        # Check compliance (Final Report)
        print("\n" + "="*50)
        print(f"COMPLIANCE RESULT:")
        print("="*50)
        print(compliance_results)


##################   Prompt for OpenAI Model   ##########################


system_prompt_json = """
You are a helpful assistant that extracts informations on pdf files.

### Instructions:
  - You have one resource: a pdf file containing a laboratory report from an eu laboratory. It can be in any language.
  - You have to extract relevant information from this pdf file, and issue a report in JSON format in English
  - First, identify the name of the product tested
  - Then, translate the name of the product in English
  - Then, for each product, identify the list of substances detected in the report. There can be one or several substances.
  - Then, for each substance, identify its name and translate it in English 
  - Finally, for each substance, identify the measure MRL written in the report.
  - The output must be a JSON object with the following structure:
    {
        "Product": "name of the product in the document language",
        "Product_EU": "name of the product in English",
        "Substances": [
        {
            "Name": "name of the substance in the document language",
            "Name_EU": "name of the substance in English",
            "MRL": "value of the MRL as written in the report"
        },
        ...
        ]
    }
    - If you cannot find a value, put "Not found"
    - Return ONLY the JSON object, no additional text.
""".strip()

