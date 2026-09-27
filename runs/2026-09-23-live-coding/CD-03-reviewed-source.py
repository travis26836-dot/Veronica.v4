def find_user(conn, display_name):
    """Fetch user row(s) by display_name, safely handling untrusted input."""
    cursor = conn.cursor()
    query = "SELECT id, display_name FROM users WHERE display_name = ?"
    cursor.execute(query, (display_name,))
    results = cursor.fetchall()
    return results