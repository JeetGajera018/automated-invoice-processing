import pytesseract

from preprocessing import preprocess_image


VERTICAL_TOLERANCE = 15


COLUMN_REGIONS = {
    "no": (150, 220),
    "description": (220, 650),
    "qty": (650, 730),
    "um": (730, 850),
    "net_price": (850, 1000),
    "net_worth": (1000, 1180),
    "vat": (1180, 1350),
    "gross_worth": (1350, 1500)
}


def words_to_text(words):
    return " ".join(word["text"] for word in words)


def extract_invoice_items(image_path):

  
    # 1. PREPROCESS IMAGE


    binary = preprocess_image(image_path)


    
    # 2. OCR
    

    text2 = pytesseract.image_to_data(
        binary,
        output_type=pytesseract.Output.DICT
    )

    raw_text = pytesseract.image_to_string(binary)

   
    # 3. EXTRACT WORD-LEVEL OCR DATA


    word_data = []

    for i in range(len(text2["text"])):

        if text2["level"][i] == 5:

            if text2["text"][i].strip():

                word_data.append({
                    "text": text2["text"][i],
                    "left": text2["left"][i],
                    "top": text2["top"][i],
                    "width": text2["width"][i],
                    "height": text2["height"][i],
                    "confidence": text2["conf"][i],
                    "line_num": text2["line_num"][i],
                })


  
    # 4. SORT WORDS BY VERTICAL POSITION
  

    sorted_word_data = sorted(
        word_data,  
        key=lambda x: x["top"]
    )   


    
    # 5. GROUP WORDS INTO VISUAL ROWS
   

    rows = []

    for word in sorted_word_data:

        word_top = word["top"]

        matched_row = None

        for row in rows:

            row_top = row["top"]

            if abs(word_top - row_top) <= VERTICAL_TOLERANCE:

                matched_row = row

                matched_row["words"].append(word)

                break

        if matched_row is None:

            rows.append({
                "top": word_top,
                "words": [word]
            })


  
    # 6. SORT WORDS INSIDE EACH ROW LEFT TO RIGHT


    for row in rows:

        row["words"] = sorted(
            row["words"],
            key=lambda x: x["left"]
        )



    # 7. IDENTIFY TABLE ROWS


    table_rows = []

    for row in rows:

        row_text = " ".join(
            word["text"]
            for word in row["words"]
        )

        # Stop when invoice summary begins
        if "SUMMARY" in row_text:

            break


        # Invoice item table begins around this vertical position
        if row["top"] >= 900:

            row_data = {
                "no": [],
                "description": [],
                "qty": [],
                "um": [],
                "net_price": [],
                "net_worth": [],
                "vat": [],
                "gross_worth": []
            }


          
            # 8. ASSIGN WORDS TO TABLE COLUMNS
         

            for word in row["words"]:

                x = word["left"]

                for column, (start, end) in COLUMN_REGIONS.items():

                    if start <= x < end:

                        row_data[column].append(word)

                        break


            table_rows.append(row_data)



    # 9. GROUP MULTI-LINE TABLE ROWS INTO ITEMS
   

    items = []

    current_item = None

    for row in table_rows:

        # A row containing an invoice number starts a new item
        if row["no"]:

            current_item = {
                "no": row["no"],
                "description": row["description"].copy(),
                "qty": row["qty"],
                "um": row["um"],
                "net_price": row["net_price"],
                "net_worth": row["net_worth"],
                "vat": row["vat"],
                "gross_worth": row["gross_worth"]
            }

            items.append(current_item)


        # Otherwise, this is a continuation row
        else:

            if current_item is not None:

                current_item["description"].extend(
                    row["description"]
                )



    # 10. CONVERT OCR WORD LISTS INTO TEXT
    

    extracted_items = []

    for item in items:

        extracted_items.append({

            "no": words_to_text(item["no"]),

            "description": words_to_text(
                item["description"]
            ),

            "qty": words_to_text(
                item["qty"]
            ),

            "um": words_to_text(
                item["um"]
            ),

            "net_price": words_to_text(
                item["net_price"]
            ),

            "net_worth": words_to_text(
                item["net_worth"]
            ),

            "vat": words_to_text(
                item["vat"]
            ),

            "gross_worth": words_to_text(
                item["gross_worth"]
            )
        })


    return {
        "raw_text": raw_text,
        "items": extracted_items
    }






if __name__ == "__main__":

    image_path = "data/raw_images/batch_1/batch_1/batch1_3/batch1-1004.jpg"

    result = extract_invoice_items(image_path)

    print("\nRAW OCR TEXT:")
    print(result["raw_text"])

    print("\nEXTRACTED INVOICE ITEMS:")

    for item in result["items"]:
        print(item)