def calculate_final_price(original_price, discount_percent):
    """
    Calculate the total cost after applying a discount.

    Args:
        original_price (float): The starting price of the item.
        discount_percent (float): The discount as a percentage (e.g., 10 for 10%).

    Returns:
        float: The final price after the discount is subtracted.
    """
    # Using snake_case for internal variables
    discount_amount = original_price * (discount_percent / 100)
    final_price = original_price - discount_amount
    
    return final_price

# Example usage
laptop_price = 1200.00
sale_discount = 15.0

result = calculate_final_price(laptop_price, sale_discount)

print(f"The final price is: ${result:.2f}")
