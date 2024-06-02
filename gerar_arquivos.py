# Generating key-value files for nodes

# Key-value data for each node
key_values = {
    "key_value1.txt": [("Katharine_Hepburn", 4), ("Frances_McDormand", 3)],
    "key_value2.txt": [("Emma_Stone", 2), ("Ingrid_Bergman", 2)],
    "key_value3.txt": [("Jane_Fonda", 2), ("Meryl_Streep", 5)],
    "key_value4.txt": [("Audrey_Hepburn", 1), ("Julie_Andrews", 3)],
    "key_value5.txt": [("Bette_Davis", 4), ("Vivien_Leigh", 3)],
    "key_value6.txt": [("Grace_Kelly", 2), ("Sophia_Loren", 2)],
    "key_value7.txt": [("Elizabeth_Taylor", 5), ("Marilyn_Monroe", 4)]
}

# Writing the key-value pairs to files
for filename, pairs in key_values.items():
    with open(f"C:/Users/palaz/EP_DSID/lucca_values/{filename}", 'w') as f:
        for key, value in pairs:
            f.write(f"{key} {value}\n")
