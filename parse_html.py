from bs4 import BeautifulSoup
def style_table(filename: str) -> None:
    # --- 1. Read the original HTML file ---
    try:
        with open(filename, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"Error: {filename} not found. Make sure the file is in the same directory.")
        exit()

    # --- 2. Parse the HTML with BeautifulSoup ---
    soup = BeautifulSoup(html_content, "html.parser")

    # --- 3. Create CSS styles for the new look ---
    # This style block includes the black background, white font,
    # table borders, zebra-striping, and centered text for specific columns.
    style_code = """
        body {
            background-color: #121212; /* A very dark grey is often easier on the eyes than pure black */
            color: #FFFFFF;
            font-family: Arial, sans-serif;
        }
        table {
            width: 100%;
            border-collapse: collapse; /* Removes space between cell borders */
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #444444; /* Darker border for the theme */
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #333333; /* Header background */
        }
        /* Zebra-striping for data rows */
        tbody tr:nth-child(even) {
            background-color: #222222;
        }
        tbody tr:hover {
            background-color: #444444; /* Highlight row on hover */
        }
        /* Center the text in these specific columns */
        .center-text {
            text-align: center;
        }
    """

    # Create a <style> tag and add it to the HTML <head>
    # If <head> doesn't exist, we create it.
    head = soup.find("head")
    if not head:
        head = soup.new_tag("head")
        if soup.html:
            soup.html.insert(0, head)
        else:
            soup.insert(0, head)

    style_tag = soup.new_tag("style")
    style_tag.string = style_code
    head.append(style_tag)

    # --- 4. Center specific columns by adding a class ---
    header_row = soup.find("thead").find("tr")
    for th in header_row.find_all("th")[2:6]:  # Columns 3 to 6
        th["class"] = "center-text"

    data_rows = soup.find("tbody").find_all("tr")
    for row in data_rows:
        for td in row.find_all("td")[2:6]:  # Columns 3 to 6
            td["class"] = "center-text"


    # --- 5. Restructure the first column for perfect centering ---
    # We iterate through each row in the table body
    for row in soup.select("tbody tr"):
        first_cell = row.find("td")
        if first_cell:
            # Extract the name (text) and the image tag
            name = first_cell.find(string=True, recursive=False).strip()
            image = first_cell.find("img")

            if name and image:
                # Clear the original cell content
                first_cell.clear()

                # Create a new <div> with flexbox styles for centering
                flex_div = soup.new_tag(
                    "div",
                    style="display: flex; align-items: center; justify-content: center; gap: 10px;",
                )

                # Create a <span> for the name
                name_span = soup.new_tag("span")
                name_span.string = name

                # Add the name and image into the new div
                flex_div.append(name_span)
                flex_div.append(image)

                # Put the new div back into the cell
                first_cell.append(flex_div)

    # --- 6. Save the new HTML to a file ---
    new_html_content = soup.prettify()
    with open("styled_table.html", "w", encoding="utf-8") as f:
        f.write(new_html_content)

    print("Successfully created 'styled_table.html' with the new styles!")