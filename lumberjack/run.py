#!/usr/bin/env python
from lumber import lumber , db

if __name__ == "__main__":
    db.create_all()
    lumber.run(debug=True)
