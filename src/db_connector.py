import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.sql import func

Base = declarative_base()


# database session
# invte link
# invite link increase point message
# add field joined at for user table

# todo : /help
# todo : file converting
# todo : description of channel
# todo : attention for low credit message
# todo : fix command loop
# todo : zarrinpaal


class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True)
    credit = Column(Integer, default=3)
    invite_link = Column(Text)
    joined_at = Column(DateTime, default=func.now(), nullable=True, )


class Images(Base):
    __tablename__ = 'images'

    image_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    image_description = Column(Text)
    resolution = Column(Text(length=20))
    quality = Column(Text(length=20))
    image_url = Column(Text)
    generation_date = Column(DateTime, default=func.now())


class Messages(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    datetime = Column(DateTime, default=datetime.now)
    user_id = Column(Integer)


class Transaction(Base):
    __tablename__ = 'transaction'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    amount = Column(Integer)
    description = Column(Text, nullable=True)
    ref_id = Column(Text, nullable=True)
    authority = Column(Text, )
    status = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), )


#
# db_engine = create_engine('sqlite:///./../db.sqlite3', echo=True)
# Base.metadata.create_all(db_engine)


# Define the database operations class
class DatabaseOperations:
    db_engine = create_engine('sqlite:///./../db.sqlite3', echo=True)
    Session = sessionmaker(bind=db_engine)
    session = Session()

    def __init__(self):
        pass

    @classmethod
    def get_user_credit(cls, user_id):
        user = cls.session.query(User).filter_by(user_id=user_id).first()
        if user:
            return user.credit
        else:
            cls.create_message(user_id, f"user with this id doesn't exist {user_id}")
            new_user = cls.add_user(user_id)
            return new_user.credit

    @classmethod
    def is_user_exists(cls, user_id):
        user = cls.session.query(User).filter_by(user_id=user_id).first()
        return user is not None

    @classmethod
    def add_user(cls, user_id, credit=3):
        existing_user = cls.session.query(User).filter_by(user_id=user_id).first()
        if existing_user:
            print(f"User with ID {user_id} already exists.")
            return existing_user
        invite_token = str(uuid.uuid4())
        new_user = User(user_id=user_id, credit=credit, invite_link=invite_token)
        cls.session.add(new_user)
        cls.session.commit()
        return new_user

    @classmethod
    def update_user_credit(cls, user_id, new_credit):
        user = cls.session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.credit = new_credit
            cls.session.commit()
            return user
        return None

    @classmethod
    def increase_user_credit(cls, user_id, amount):
        user = cls.session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.credit += amount
            cls.session.commit()
            return user
        return None

    @classmethod
    def decrease_user_credit(cls, user_id, amount):
        user = cls.session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.credit -= amount
            cls.session.commit()
            return user

    @classmethod
    def delete_user(cls, user_id):
        user = cls.session.query(User).filter_by(user_id=user_id).first()
        if user:
            cls.session.delete(user)
            cls.session.commit()
            return user
        return None

    @classmethod
    def get_user_invite_link(cls, user_id):
        user = cls.session.query(User).filter_by(user_id=user_id).first()
        return user.invite_link if user else None

    @classmethod
    def create_image(cls, user_id, prompt, size, quality, image_url):
        new_image = Images(
            user_id=user_id,
            image_description=prompt,
            resolution=size,
            quality=quality,
            image_url=image_url,
            generation_date=datetime.now()
        )
        cls.session.add(new_image)
        cls.session.commit()
        return new_image

    @classmethod
    def get_user_images(cls, user_id) -> list:
        with cls.Session() as session:
            # Fetch the images
            images = session.query(Images).filter_by(user_id=user_id).all()
            # Convert the generation_date to a string representation
            # for image in images:
            #     image.generation_date = image.generation_date.isoformat() if image.generation_date else None
            return images

    @classmethod
    def create_message(cls, user_id, content):
        new_message = Messages(
            user_id=user_id,
            content=content
        )
        cls.session.add(new_message)
        cls.session.commit()
        return new_message

    @classmethod
    def get_user_by_invite_link(cls, invite_link):
        with cls.Session() as session:
            user = session.query(User).filter_by(invite_link=invite_link).first()
            return user.user_id if user else None

    @classmethod
    def get_image_url(cls, image_id):
        with cls.Session() as session:
            image = session.query(Images).filter_by(image_id=image_id).first()
            return image.image_url if image else None

    @classmethod
    def create_transaction(cls, user_id, amount, authority):
        new_transaction = Transaction(
            user_id=user_id,
            amount=amount,
            authority=authority,
            created_at=datetime.now()  # You might want to timestamp the transaction creation
        )

        cls.session.add(new_transaction)
        cls.session.commit()
        return new_transaction

    @classmethod
    def update_transaction(cls, authority, status, ref_id):
        transaction = cls.session.query(Transaction).filter_by(authority=authority).first()
        if transaction:
            transaction.status = status
            transaction.ref_id = ref_id
            transaction.updated_at = datetime.now()
            cls.session.commit()
            return transaction
        return None
