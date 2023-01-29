import shutil
from datetime import datetime
from fastapi import FastAPI, Response, Request, Depends, Form, HTTPException, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import engine, User, Relationship, Sex, LookingFor, PoliticalView, RelationshipStatus, SchoolStatus
from app.auth import AuthHandler
from sqlmodel import Session, select, or_

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
def login(*, response: Response, session: Session = Depends(get_db_session), email: str=Form(), password: str=Form()):
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
    
    stmt = select(Relationship).where(Relationship.confirmed == True).where(or_(Relationship.sender_id == user.id, Relationship.reciever_id == user.id))
    results = session.exec(stmt).all()

    my_friends = []
    if len(results) > 0:
        for r in results:
            if r.sender_id == user.id:
                friend = session.get(User, r.reciever_id)
            elif r.reciever_id == user.id:
                friend = session.get(User, r.sender_id)
            result = {
                "id": friend.id,
                "picture_src": friend.picture_src,
                "name": friend.name
            }
            my_friends.append(result)

    stmt = select(Relationship).where(Relationship.reciever_id == user.id).where(Relationship.confirmed == False)
    results = session.exec(stmt).all()
    my_requests = len(results) if len(results) > 0 else 0
    
    my_messages = 0
    context = {
        "request": request,
        "user": user,
        "my_friends": my_friends,
        "my_requests": my_requests,
        "my_messages": my_messages
    }
    return templates.TemplateResponse("loged_in/profile.html", context)

@app.get("/profile/{id}", response_class=HTMLResponse)
def get_home_page(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper), id:int):
    viewer = session.get(User, user_id)
    
    stmt = select(Relationship).where(Relationship.reciever_id == viewer.id).where(Relationship.confirmed == False)
    results = session.exec(stmt).all()
    my_requests = len(results) if len(results) > 0 else 0
    
    my_messages = 0
    
    profile_owner = session.get(User, id)

    stmt = select(Relationship).where(Relationship.confirmed == True).where(or_(Relationship.sender_id == profile_owner.id, Relationship.reciever_id == profile_owner.id))
    results = session.exec(stmt).all()

    my_friends = []
    if len(results) > 0:
        for r in results:
            if r.sender_id == profile_owner.id:
                friend = session.get(User, r.reciever_id)
            elif r.reciever_id == profile_owner.id:
                friend = session.get(User, r.sender_id)
            result = {
                "id": friend.id,
                "picture_src": friend.picture_src,
                "name": friend.name
            }
            my_friends.append(result)

    context = {
        "request": request,
        "viewer": viewer,
        "user": profile_owner,
        "my_friends": my_friends,
        "my_requests": my_requests,
        "my_messages": my_messages
    }
    return templates.TemplateResponse("loged_in/profileid.html", context)


@app.get("/profile", response_class=HTMLResponse)
def get_edit_profile_page(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper)):
    user = session.get(User, user_id)
    
    stmt = select(Relationship).where(Relationship.reciever_id == user.id).where(Relationship.confirmed == False)
    results = session.exec(stmt).all()
    my_requests = len(results) if len(results) > 0 else 0
    
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
    user.last_update = datetime.now()

    session.commit()
    session.refresh(user)
    return RedirectResponse(url=app.url_path_for("get_home_page"), status_code=status.HTTP_303_SEE_OTHER)

@app.get("/picture", response_class=HTMLResponse)
def get_picture_page(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper)):
    my_messages = 0
    user = session.get(User, user_id)
    stmt = select(Relationship).where(Relationship.reciever_id == user.id).where(Relationship.confirmed == False)
    results = session.exec(stmt).all()
    my_requests = len(results) if len(results) > 0 else 0


    context = {
        "request": request,
        "current_picture": user.picture_src,
        "my_requests": my_requests,
        "my_messages": my_messages
    }
    
    return templates.TemplateResponse("loged_in/picture.html", context)

@app.post("/picture")
def upload_picture(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper), picture_file: UploadFile=File(...)):
    user = session.get(User, user_id)
    
    file_extension = picture_file.filename[picture_file.filename.rfind("."):]
    picture_src = f"{user_id}{file_extension}"

    picture_destination_file = f"static/profile_img/{picture_src}"

    with open(picture_destination_file , "wb") as buffer:
         shutil.copyfileobj(picture_file.file, buffer)

    user.picture_src = picture_src
    session.commit()
    session.refresh(user)
    return RedirectResponse(url=app.url_path_for("get_home_page"), status_code=status.HTTP_303_SEE_OTHER)

@app.get("/search", response_class=HTMLResponse)
def get_search_page(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper)):
    user = session.get(User, user_id)
    stmt = select(Relationship).where(Relationship.reciever_id == user.id).where(Relationship.confirmed == False)
    results = session.exec(stmt).all()
    my_requests = len(results) if len(results) > 0 else 0
    my_messages = 0

    context = {
        "request": request,
        "my_requests": my_requests,
        "my_messages": my_messages,
        "search_results": None
    }
    return templates.TemplateResponse("loged_in/search.html", context)


@app.post("/search", response_class=HTMLResponse)
def search_users(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper), search_field:str=Form(), search_query:str=Form()):
    user = session.get(User, user_id)
    stmt = select(Relationship).where(Relationship.reciever_id == user.id).where(Relationship.confirmed == False)
    results = session.exec(stmt).all()
    my_requests = len(results) if len(results) > 0 else 0
    my_messages = 0
    
    if search_field == "name":
        stmt = select(User).where(User.name == search_query)
    if search_field == "email":
        stmt = select(User).where(User.email == search_query)
    if search_field == "school":
        stmt = select(User).where(User.school == search_query)
    if search_field == "school_status":
        stmt = select(User).where(User.school_status == search_query)
    if search_field == "sex":
        stmt = select(User).where(User.sex == search_query)
    if search_field == "residence":
        stmt = select(User).where(User.residence == search_query)
    
    results = session.exec(stmt).all()
    
    search_results = []
    if len(results) > 0:
        for r in results:
            if r.id == user_id:
                continue
            result = {
                "id": r.id,
                "picture_src": r.picture_src,
                "name": r.name,
                "school": r.school,
                "residence": r.residence
            }
            search_results.append(result)

    context = {
        "request": request,
        "my_requests": my_requests,
        "my_messages": my_messages,
        "search_results": search_results
    }

    return templates.TemplateResponse("loged_in/search.html", context)


@app.get("/invite", response_class=HTMLResponse)
def get_invite_page(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper)):
    user = session.get(User, user_id)
    stmt = select(Relationship).where(Relationship.reciever_id == user.id).where(Relationship.confirmed == False)
    results = session.exec(stmt).all()
    my_requests = len(results) if len(results) > 0 else 0
    my_messages = 0
    
    stmt = select(Relationship).where(Relationship.sender_id == user.id).where(Relationship.confirmed == False)
    results = session.exec(stmt).all()
    my_invites = []

    if len(results) > 0:
        for r in results:
            reciever = session.get(User, r.reciever_id)
            result = {
                "id": reciever.id,
                "picture_src": reciever.picture_src,
                "name": reciever.name,
                "school": reciever.school,
                "residence": reciever.residence
            }
            my_invites.append(result)

    context = {
        "request": request,
        "user": user,
        "my_requests": my_requests,
        "my_messages": my_messages,
        "my_invites": my_invites
    }
    return templates.TemplateResponse("loged_in/invites.html", context)


@app.get("/invite/{id}")
def send_invite(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper), id:int):
    user = session.get(User, user_id)

    friendship = Relationship(sender_id=user.id, reciever_id=id)
    session.add(friendship)
    session.commit()
    session.refresh(friendship)

    return RedirectResponse(url=app.url_path_for("get_invite_page"), status_code=status.HTTP_303_SEE_OTHER)

@app.get("/invite/cancel/{id}")
def cancel_invite(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper), id:int):
    user = session.get(User, user_id)

    stmt = select(Relationship).where(Relationship.sender_id == user.id).where(Relationship.reciever_id == id)
    result = session.exec(stmt).first()
   
    session.delete(result)
    session.commit()

    return RedirectResponse(url=app.url_path_for("get_invite_page"), status_code=status.HTTP_303_SEE_OTHER)

@app.get("/requests", response_class=HTMLResponse)
def get_requests_page(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper)):
    user = session.get(User, user_id)
    my_messages = 0
    
    stmt = select(Relationship).where(Relationship.reciever_id == user.id).where(Relationship.confirmed == False)
    results = session.exec(stmt).all()
    my_requests = len(results) if len(results) > 0 else 0
    
    my_requests_list = []

    if len(results) > 0:
        for r in results:
            sender = session.get(User, r.sender_id)
            result = {
                "id": sender.id,
                "picture_src": sender.picture_src,
                "name": sender.name,
                "school": sender.school,
                "residence": sender.residence
            }
            my_requests_list.append(result)

    context = {
        "request": request,
        "user": user,
        "my_requests": my_requests,
        "my_messages": my_messages,
        "my_requests_list": my_requests_list
    }
    return templates.TemplateResponse("loged_in/requests.html", context)

@app.get("/requests/accept/{id}")
def cancel_invite(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper), id:int):
    user = session.get(User, user_id)

    stmt = select(Relationship).where(Relationship.sender_id == id).where(Relationship.reciever_id == user.id)
    relationship = session.exec(stmt).first()
    
    relationship.confirmed = True
    session.commit()

    return RedirectResponse(url=app.url_path_for("get_requests_page"), status_code=status.HTTP_303_SEE_OTHER)

@app.get("/friends", response_class=HTMLResponse)
def get_friends_page(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper)):
    user = session.get(User, user_id)
    my_messages = 0
    
    stmt = select(Relationship).where(Relationship.confirmed == True).where(or_(Relationship.sender_id == user.id, Relationship.reciever_id == user.id))
    results = session.exec(stmt).all()

    my_friends = []
    if len(results) > 0:
        for r in results:
            if r.sender_id == user.id:
                friend = session.get(User, r.reciever_id)
            elif r.reciever_id == user.id:
                friend = session.get(User, r.sender_id)
            result = {
                "id": friend.id,
                "picture_src": friend.picture_src,
                "name": friend.name
            }
            my_friends.append(result)


    stmt = select(Relationship).where(Relationship.reciever_id == user.id).where(Relationship.confirmed == False)
    results = session.exec(stmt).all()
    my_requests = len(results) if len(results) > 0 else 0
    
    my_requests_list = []

    if len(results) > 0:
        for r in results:
            sender = session.get(User, r.sender_id)
            result = {
                "id": sender.id,
                "picture_src": sender.picture_src,
                "name": sender.name,
                "school": sender.school,
                "residence": sender.residence
            }
            my_requests_list.append(result)

    context = {
        "request": request,
        "user": user,
        "my_requests": my_requests,
        "my_messages": my_messages,
        "my_friends": my_friends
    }
    return templates.TemplateResponse("loged_in/friends.html", context)

@app.get("/friends/{id}", response_class=HTMLResponse)
def get_friends(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper), id:int):
    viewer = session.get(User, id)
    
    stmt = select(Relationship).where(Relationship.reciever_id == viewer.id).where(Relationship.confirmed == False)
    results = session.exec(stmt).all()
    my_requests = len(results) if len(results) > 0 else 0
    
    my_messages = 0
    
    profile_owner = session.get(User, id)

    stmt = select(Relationship).where(Relationship.confirmed == True).where(or_(Relationship.sender_id == profile_owner.id, Relationship.reciever_id == profile_owner.id))
    results = session.exec(stmt).all()

    my_friends = []
    if len(results) > 0:
        for r in results:
            if r.sender_id == profile_owner.id:
                friend = session.get(User, r.reciever_id)
            elif r.reciever_id == profile_owner.id:
                friend = session.get(User, r.sender_id)
            result = {
                "id": friend.id,
                "picture_src": friend.picture_src,
                "name": friend.name
            }
            my_friends.append(result)

    context = {
        "request": request,
        "viewer": viewer,
        "user": profile_owner,
        "my_friends": my_friends,
        "my_requests": my_requests,
        "my_messages": my_messages
    }
    return templates.TemplateResponse("loged_in/friendsid.html", context)

@app.get("/friends/remove/{id}")
def remove_friend(*, request: Request, session: Session=Depends(get_db_session), user_id=Depends(auth_handler.auth_wrapper), id:int):
    user = session.get(User, user_id)

    stmt = select(Relationship).where(Relationship.sender_id == user.id).where(Relationship.reciever_id == id)
    result = session.exec(stmt).first()
   
    session.delete(result)
    session.commit()

    return RedirectResponse(url=app.url_path_for("get_friends_page"), status_code=status.HTTP_303_SEE_OTHER)