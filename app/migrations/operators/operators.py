def build_condition(key_data):
    return " AND ".join("{col}='{value}'".format(col=col, value=value) for col, value in key_data.items())