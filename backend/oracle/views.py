from django.http import JsonResponse
from django.db import connection

def testfunction(request):
    with connection.cursor() as cursor:
        # Execute raw SQL query
        cursor.execute("SELECT * FROM test_table;")
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]  # Get column names

        # Format the result as a list of dictionaries
        result = [dict(zip(columns, row)) for row in rows]

    return JsonResponse(result, safe=False)