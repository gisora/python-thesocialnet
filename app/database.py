from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, create_engine
from enum import Enum


DB_FILE_NAME = "database.sqlite"
DB_URL = f"sqlite:///{DB_FILE_NAME}"


class AccountStatus(str, Enum):
    registered = "Registered"
    confirmed = "Confirmed"
    school_admin = "School Admin"
    super_admin = "Super Admin"
    deactivated = "Deactivated"
    

class LookingFor(str, Enum):
    friendship = "Friendship"
    relationship = "Relationship"
    hooking_up = "Hooking-up"
    moral_support = "Moral Support"
    parties = "Parties"
    

class MessageStatus(str, Enum):
    sent = "Sent"
    read = "Read"
    replied = "Replied"
    

class PoliticalView(str, Enum):
    very_liberal = "Very Liberal"
    liberal = "Liberal"
    middle_of_the_road = "Middle of the road"
    conservative = "Conservative"
    very_conservative = "Very Conservative"


class RelationshipType(str, Enum):
    friends = "Friends"
    casually_dating = "Casually dating"
    in_a_serious_relationship = "In a serious relationship"
    friends_with_benefits = "Friends with benefits"
    best_friends = "Best Friends"
    rivals = "Rivals"
    enemies = "Enemies"
    engaged = "Engaged"
    married = "Married"

class RelationshipStatus(str, Enum):
    single = "Single"
    dating = "Dating"
    engaged = "Engaged"
    married = "Married"
    divorced = "Divorced"


class SchoolStatus(Enum):
    student = "Student"
    alumnus = "Alumnus/Alumna"
    faculty = "Faculty"
    staff = "Staff"


class Sex(str, Enum):
    female = "Female"
    male = "Male"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str   # TODO turi buti unique
    password: str
    created: datetime = Field(default=datetime.today())
    account_status: Optional[AccountStatus] = Field(default=AccountStatus.confirmed)
    last_update: Optional[datetime]
    picture_src: str = Field(default="default.png")
    school: Optional[str]
    school_status: SchoolStatus
    sex: Optional[Sex] 
    residence: Optional[str]
    birthday: Optional[datetime]
    home_town: Optional[str]
    highschool: Optional[str]
    screenname: Optional[str]
    mobile: Optional[str]
    website: Optional[str]
    # TODO sqlite doesnt store lists
    looking_for: Optional[str]
    interested_in: Optional[str] # ENUM
    relationship_status: Optional[str]
    political_views: Optional[PoliticalView]
    interests: Optional[str]
    music: Optional[str]
    classes: Optional[str]
    fridge: Optional[str]


class Relationship(SQLModel, table=True):
    sender_id: int = Field(default=None, foreign_key="user.id", primary_key=True)
    reciever_id: int = Field(default=None, foreign_key="user.id", primary_key=True)
    type: RelationshipType = Field(default=RelationshipType.friends)
    confirmed: bool = Field(default=False)


engine = create_engine(DB_URL)


def create_all_tables():
    SQLModel.metadata.create_all(engine)


def load_demo_data():
    pass

if __name__ == "__main__":
    create_all_tables()
    # load_demo_Data