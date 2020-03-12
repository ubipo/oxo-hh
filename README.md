# oxo-hh

Demonstrative oxo game using pygame.
Part of a teaching assignment.

The multiplayer component (oxo_single_solution.py) uses [mqtt](https://en.wikipedia.org/wiki/MQTT) for game "rooms".
Two players that want to play together connect to the same mqtt topic and publish their respective moves.

Because the networking component is meant to be hidden from the students it's zero-configuration.
This means you have to create a server_address.py file like:
```python
host = "example.net"
port = 1883
```
