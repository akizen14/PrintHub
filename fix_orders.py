"""Fix orders.json to ensure all orders have filePath"""
import json

# Read the database
with open('data/orders.json', 'r') as f:
    data = json.load(f)

# Fix each order
for key, order in data['_default'].items():
    order_id = order.get('id')
    file_name = order.get('fileName', '')
    
    # If filePath is missing or empty, construct it
    if not order.get('filePath'):
        # Determine the PDF filename
        if file_name.lower().endswith('.pdf'):
            pdf_name = file_name
        else:
            # Replace extension with .pdf
            pdf_name = file_name.rsplit('.', 1)[0] + '.pdf' if '.' in file_name else file_name + '.pdf'
        
        order['filePath'] = f"C:\\PrintHub\\Orders\\{order_id}\\{pdf_name}"
        print(f"Fixed order {order_id}: {order['filePath']}")

# Write back
with open('data/orders.json', 'w') as f:
    json.dump(data, f, indent=2)

print("\nDone! All orders now have filePath.")
