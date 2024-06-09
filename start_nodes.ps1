Start-Process "cmd" -ArgumentList "/k python node.py 127.0.0.1:5001 topologia_linha/1.txt key_values/key_value1.txt"
Start-Process "cmd" -ArgumentList "/k python node.py 127.0.0.1:5002 topologia_linha/2.txt key_values/key_value2.txt"
Start-Process "cmd" -ArgumentList "/k python node.py 127.0.0.1:5003 topologia_linha/3.txt key_values/key_value3.txt"