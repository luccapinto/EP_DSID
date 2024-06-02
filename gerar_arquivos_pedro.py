# Generating key-value files for Pedras nodes

# Key-value data for each Pedras node
key_values_pedras = {
    "key_value_pedras_1.txt": [("Pedras_Katharine_Hepburn", 19), ("Pedras_Julie_Andrews", 20)],
    "key_value_pedras_2.txt": [("Pedras_Emma_Stone", 21), ("Pedras_Sophia_Loren", 22)],
    "key_value_pedras_3.txt": [("Pedras_Jane_Fonda", 23), ("Pedras_Audrey_Hepburn", 24)],
    "key_value_pedras_4.txt": [("Pedras_Frances_McDormand", 25), ("Pedras_Vivien_Leigh", 26)],
    "key_value_pedras_5.txt": [("Pedras_Bette_Davis", 27), ("Pedras_Ingrid_Bergman", 28)],
    "key_value_pedras_6.txt": [("Pedras_Grace_Kelly", 29), ("Pedras_Elizabeth_Taylor", 30)],
    "key_value_pedras_7.txt": [("Pedras_Marilyn_Monroe", 31), ("Pedras_Meryl_Streep", 32)],
    "key_value_pedras_8.txt": [("Pedras_Audrey_Tautou", 33), ("Pedras_Jane_Fonda", 34)],
    "key_value_pedras_9.txt": [("Pedras_Emma_Watson", 35), ("Pedras_Frances_McDormand", 36)]
}

# Writing the key-value pairs to files
for filename, pairs in key_values_pedras.items():
    with open(f"C:/Users/palaz/EP_DSID/pedras_values/{filename}", 'w') as f:
        for key, value in pairs:
            f.write(f"{key} {value}\n")