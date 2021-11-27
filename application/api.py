from main import app
from flask import make_response
from flask_restful import Resource, Api
from main import db, Cards, UserDecks, Decks, DeckCards, User
from flask_restful import HTTPException, reqparse, fields, marshal_with
import json
api = Api(app)

# --------------------- Validation -------------------

class Error(HTTPException):
    def __init__(self, message, status_code):
        self.response = make_response(message, status_code)

# -------------------- API Resource ---------------------

card_fields = {
    'card_id': fields.Integer, 
    'front': fields.String,
    'back': fields.String
}

deck_fields = {
    'deck_id': fields.Integer, 
    'name': fields.String,
    'score': fields.Integer,
    'last_reviewed': fields.DateTime(dt_format='rfc822')
}

card_parser = reqparse.RequestParser()
card_parser.add_argument('front')
card_parser.add_argument('back')

deck_parser = reqparse.RequestParser()
deck_parser.add_argument('name')


class DeckAPI(Resource):
    @marshal_with(deck_fields)
    def get(self, deck_id):
        try:
            deck = Decks.query.filter_by(deck_id=deck_id).first()
        except: 
            raise Error(message="Internal Server Error", status_code=500)        
        if deck is None:
            raise Error(message ="Deck not found", status_code=404) 
        else:
            return deck, 200
    
    @marshal_with(deck_fields)
    def put(self, deck_id):
        args = deck_parser.parse_args()
        name = args['name']

        # Argument Handling
        if name is None or name == '':
            raise Error(message = 'Deck Name is required', status_code=400)
        try:
            deck = Decks.query.filter_by(deck_id=deck_id).first()
        except:
            raise Error(message="Internal Server Error", status_code=500)

        if deck is None:
            raise Error(message="Deck not found", status_code=404)
        
        deck.name = name
        db.session.commit()
        return deck, 200

    def delete(self, deck_id):
        try:
            deck = Decks.query.filter_by(deck_id=deck_id).first()
        except:
            raise Error(message="Internal Server Error", status_code=500)

        if deck is None:
            raise Error(message="Deck not found", status_code=404)

        deck_cards = DeckCards.query.filter_by(deck_id = deck_id).all()
        for deck_card in deck_cards:
            card = Cards.query.filter_by(card_id = deck_card.card_id).first()
            db.session.delete(deck_card)
            db.session.delete(card)

        user_deck = UserDecks.query.filter_by(deck_id = deck_id).first()
        db.session.delete(user_deck)

        db.session.delete(deck)
        db.session.commit()
        return "Successfully Deleted", 200
    
    @marshal_with(deck_fields)    
    def post(self):
        args = deck_parser.parse_args()
        name = args['name']

        # Argument Handling
        if name is None or name == '':
            raise Error(message = 'Deck Name is required', status_code=400)
        
        new_deck = Decks(name=name)
        db.session.add(new_deck)
        db.session.commit()
        return new_deck, 201

class CardAPI(Resource):
    @marshal_with(card_fields)
    def get(self, card_id):
        try:
            card = Cards.query.filter_by(card_id=card_id).first()
        except: 
            raise Error(message="Internal Server Error", status_code=500)        
        if card is None:
            raise Error(message ="Card not found", status_code=404) 
        else:
            return card, 200

    @marshal_with(card_fields)
    def put(self, card_id):
        args = card_parser.parse_args()
        front = args['front']
        back = args['back']

        # Argument Handling
        if front is None or front == '':
            raise Error(message = 'Card Question ("front") is required', status_code=400)
        elif back is None or back == '':
            raise Error(message = 'Card Answer ("back") is required', status_code=400)
        try:
            card = Cards.query.filter_by(card_id=card_id).first()
        except:
            raise Error(message="Internal Server Error", status_code=500)

        if card is None:
            raise Error(message="Card not found", status_code=404)
        
        card.front = front
        card.back = back
        db.session.commit()
        return card, 200
    
    def delete(self, card_id):
        try:
            card = Cards.query.filter_by(card_id=card_id).first()
        except:
            raise Error(message="Internal Server Error", status_code=500)

        if card is None:
            raise Error(message="Card not found", status_code=404)

        deck_card = DeckCards.query.filter_by(card_id = card_id).first()
        if deck_card:
            db.session.delete(deck_card)
        db.session.delete(card)
        db.session.commit()
        return "Successfully Deleted", 200
    
    @marshal_with(card_fields)
    def post(self):
        args = card_parser.parse_args()
        front = args['front']
        back = args['back']

        # Argument Handling
        if front is None or front == '':
            raise Error(message = 'Card Question (Front) is required', status_code=400)
        elif back is None or back == '':
            raise Error(message = 'Card Answer (Back) is required', status_code=400)

        new_card = Cards(front = front, back = back, score = 0, count = 0)
        db.session.add(new_card)
        db.session.commit()
        return new_card, 201 

class UserAPI(Resource):
    def get(self, id):
        try:
            user = User.query.filter_by(id=id).first()
        except: 
            raise Error(message="Internal Server Error", status_code=500)        
        if user is None:
            raise Error(message ="User not found", status_code=404) 
        else:
            result = {}
            result["id"] = id
            result["username"] = user.username
            decks = db.session.query(User, Decks).join(UserDecks, UserDecks.user_id == User.id).join(Decks, Decks.deck_id == UserDecks.deck_id).all()
            deck_names = []
            for u, d in decks:
                if u.id == id:
                    deck_names.append(d.name)
            result["decks"] = deck_names
            return result, 200
       
        
api.add_resource(DeckAPI, '/api/deck', '/api/deck/<int:deck_id>')
api.add_resource(CardAPI, '/api/card', '/api/card/<int:card_id>')
api.add_resource(UserAPI, '/api/user/<int:id>')
