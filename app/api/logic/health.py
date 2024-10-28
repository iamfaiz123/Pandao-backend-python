def health():
    return {
        "message": "hi i am up and running",
        "status": "200"
    }


# Define initial values for the tags table
from models import Tag, dbsession as conn


def pre_define_data():
    try:  # Define initial values for the tags table
        initial_tags = [
            Tag(name='Governance'),
            Tag(name='Proposal'),
            Tag(name='Voting'),
            Tag(name='Treasury'),
            Tag(name='Membership'),
            Tag(name='Funding'),
            Tag(name='Community'),
            Tag(name='Development'),
            Tag(name='Marketing'),
            Tag(name='Legal'),
            Tag(name='Just an initial idea'),
            Tag(name='Here to explore'),
            Tag(name='Actus'),
            Tag(name='Explore'),
            Tag(name='Free'),
            Tag(name='FriendShip'),
            Tag(name='Games')
        ]

        # Insert initial values into the tags table
        conn.add_all(initial_tags)
        conn.commit()

        # Close the conn
        conn.close()
    finally:
        pass
