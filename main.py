from datetime import datetime
from fastapi import FastAPI, Response, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import engine, User, Relationship, Sex, LookingFor, PoliticalView, RelationshipStatus, SchoolStatus
from app.auth import AuthHandler
from sqlmodel import Session, select

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

auth_handler = AuthHandler()

# Function for SQLmodel DB session injection as dependencie
def get_db_session():
    with Session(engine) as session:
        yield session


@app.get("/", response_class=HTMLResponse)
def get_index_page(request: Request, loged_in: bool=False):
    context = {
        "request": request,
    }
    if loged_in:
        return templates.TemplateResponse("loged_in/home.html", context)
    else:
        return templates.TemplateResponse("loged_out/welcome.html", context)

@app.get("/register", response_class=HTMLResponse)
def get_register_page(request: Request):
    return templates.TemplateResponse("loged_out/register.html", {"request": request, "school_status_enum": SchoolStatus})

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(*, request: Request, session: Session=Depends(get_db_session), name=Form(), school_status: SchoolStatus=Form(), email=Form(), password=Form()):
    context = {
        "request": request,
        "name": name,
        "email": email,
        "school_status_enum": SchoolStatus
    }

    stmt  = select(User).where(User.email == email)
    result = session.exec(stmt).first()
    
    if result is not None:
        # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, details="User with entered email is already registered")
        return templates.TemplateResponse("loged_out/register.html", context)
    else:
        user_account = User(
            name=name,
            email=email,
            password=auth_handler.get_password_hash(password),
            school_status=school_status.value,
            created=datetime.today(),
            last_update=datetime.today()
        )
        session.add(user_account)
        session.commit()
        session.refresh(user_account)
        return templates.TemplateResponse("loged_out/login.html", context)
   

@app.get("/login", response_class=HTMLResponse)
def get_login_page(request: Request):
    return templates.TemplateResponse("loged_out/login.html", {"request": request})

@app.post("/login")
def login(*, response: Response, session: Session = Depends(get_db_session), email: str = Form(), password: str = Form()):
    stmt = select(User).where(User.email == email)
    result = session.exec(stmt).first()
    if result is None or (not auth_handler.verify_password(password, result.password)):
        # raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username and/or password")
        return RedirectResponse(url=app.url_path_for("get_login_page"), status_code=status.HTTP_303_SEE_OTHER)
    else:
        response = RedirectResponse(url=app.url_path_for("get_home_page"), status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="token", value=auth_handler.encode_token(result.id), httponly=True)
        return response
       

@app.get("/logout", response_class=HTMLResponse)
def logout(request: Request, response: Response):
    response = RedirectResponse(url=app.url_path_for("get_index_page"), status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="token", value=f"", httponly=True)
    return response


@app.get("/home", response_class=HTMLResponse)
def get_home_page(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper)):
    user = session.get(User, user_id)
    my_friends = "You have no friends :("
    my_requests = 0
    my_messages = 0
    context = {
        "request": request,
        "user": user,
        "my_friends": my_friends,
        "my_requests": my_requests,
        "my_messages": my_messages
    }
    return templates.TemplateResponse("loged_in/profile.html", context)

@app.get("/profile", response_class=HTMLResponse)
def get_edit_profile_page(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper)):
    user = session.get(User, user_id)
    my_requests = 0
    my_messages = 0

    context = {
        "request": request,
        "user": user,
        "sex_enum": Sex,
        "looking_for_enum": LookingFor,
        "political_view_enum": PoliticalView,
        "relationship_status_enum": RelationshipStatus,
        "my_requests": my_requests,
        "my_messages": my_messages
    }
    return templates.TemplateResponse("loged_in/edit_profile.html", context)

@app.post("/profile")
async def update_profile(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper)):
    form = await request.form()
    
    user = session.get(User, user_id)
    user.school = form.get("school")
    user.sex = form.get("sex")
    user.residence = form.get("residence")

    try:
        user.birthday = datetime.strptime(form.get("birthday"), ("%Y-%m-%d"))
    except ValueError:
        user.birthday = None
    
    user.home_town = form.get("home_town")
    user.highschool = form.get("highschool")
    user.screenname = form.get("screenname")
    user.mobile = form.get("mobile")
    user.website = form.get("website")
    
    looking_for = ""
    looking_for_friendship = form.get("LookingFor.friendship")
    looking_for_hooking_up = form.get("LookingFor.hooking_up")
    looking_for_moral_support = form.get("LookingFor.moral_support")
    looking_for_parties = form.get("LookingFor.parties")
    looking_for_relationship = form.get("LookingFor.relationship")
    if looking_for_friendship is not None:
        # looking_for.append(LookingFor.friendship.value)
        looking_for += LookingFor.friendship.value
    if looking_for_hooking_up is not None:
        # looking_for.append(LookingFor.hooking_up.value)
        looking_for += LookingFor.hooking_up.value
    if looking_for_moral_support is not None:
        # looking_for.append(LookingFor.moral_support.value)
        looking_for += LookingFor.moral_support.value
    if looking_for_parties is not None:
        # looking_for.append(LookingFor.parties.value)
        looking_for += LookingFor.parties.value
    if looking_for_relationship is not None:
        # looking_for.append(LookingFor.relationship.value)
        looking_for += LookingFor.relationship.value
    user.looking_for = looking_for if len(looking_for) > 0 else None

    user.interested_in = form.get("interested_in")
    user.relationship_status = form.get("relationship_status")
    user.political_views = form.get("political_views")
    user.interests = form.get("interests")
    user.music = form.get("music")
    user.classes = form.get("classes")
    user.fridge = form.get("fridge")

    session.commit()
    session.refresh(user)
    return RedirectResponse(url=app.url_path_for("get_home_page"), status_code=status.HTTP_303_SEE_OTHER)

@app.get("/picture", response_class=HTMLResponse)
def get_picture_page(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper)):
    my_requests = 0
    my_messages = 0
    user = session.get(User, user_id)
    context = {
        "request": request,
        "current_picture": user.picture_src,
        "my_requests": my_requests,
        "my_messages": my_messages
    }
    
    return templates.TemplateResponse("loged_in/picture.html", context)