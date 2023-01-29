# python-thesocialnet (PTU8 praktinis darbas Nr. 2 (DB))

## thesocialnet - mėginimass atkurti 2004 m. thefacebook versiją naudojant python

### Užduoties įdėjos ir pavyzdžiai:
- [Waybackmachine "thefacebook.com 2004-02-14 snapshot"](https://web.archive.org/web/20040212031928/http://www.thefacebook.com/)
- [thefacebook.us - clone of thefacebook.com, html by Mark Zuckerberg, php by Jeff Bachand](https://github.com/jbachand/thefacebook.us)

### Naudotos priemonės:
- python
- fastapi [ https://fastapi.tiangolo.com/ ]
- uvicorn [ https://www.uvicorn.org/ ]
- sqlmodel [ https://sqlmodel.tiangolo.com/ ]
- jinja2 [ https://palletsprojects.com/p/jinja/ ]

### Paleidimo instrukcija:
1. Sukuriam virtualią aplinką: ```python -m venv venv```
2. Aktyvuojam virtualią aplinką:
    - Linux: ```source venv/bin/activate```
    - Windows: ```venv\Scripts\activate```

3. Įdiegiam reikiamus python modulius: ```pip install -r requirements.txt```
4. Sukuriam duomenų bazę ir užpildom lenteles reikiama informacija ```pyhon app\database.py```
4. Paleidžiam uvicorn prgramą: ```uvicorn main:app```

