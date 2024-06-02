# Generating key-value files for Lucca nodes

# Key-value data for each Lucca node
key_values_lucca = {
    "key_value_lucca_1.txt": [("Lucca_Katharine_Hepburn", 1), ("Lucca_Frances_McDormand", 2)],
    "key_value_lucca_2.txt": [("Lucca_Emma_Stone", 3), ("Lucca_Ingrid_Bergman", 4)],
    "key_value_lucca_3.txt": [("Lucca_Jane_Fonda", 5), ("Lucca_Meryl_Streep", 6)],
    "key_value_lucca_4.txt": [("Lucca_Audrey_Hepburn", 7), ("Lucca_Julie_Andrews", 8)],
    "key_value_lucca_5.txt": [("Lucca_Bette_Davis", 9), ("Lucca_Vivien_Leigh", 10)],
    "key_value_lucca_6.txt": [("Lucca_Grace_Kelly", 11), ("Lucca_Sophia_Loren", 12)],
    "key_value_lucca_7.txt": [("Lucca_Elizabeth_Taylor", 13), ("Lucca_Marilyn_Monroe", 14)],
    "key_value_lucca_8.txt": [("Lucca_Audrey_Tautou", 15), ("Lucca_Monica_Bellucci", 16)],
    "key_value_lucca_9.txt": [("Lucca_Jodie_Foster", 17), ("Lucca_Cate_Blanchett", 18)]
}

# Writing the key-value pairs to files
for filename, pairs in key_values_lucca.items():
    with open(f"C:/Users/palaz/EP_DSID/lucca_values/{filename}", 'w') as f:
        for key, value in pairs:
            f.write(f"{key} {value}\n")