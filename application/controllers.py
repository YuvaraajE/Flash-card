from flask.helpers import flash
from main import app, Cards, Decks, UserDecks, DeckCards
from flask import render_template
from flask import request, url_for, redirect
from flask_security import login_required, current_user
from main import db
from random import randint
import datetime

# --------------------------- Home Page -------------------------------
@app.route("/")
@login_required
def dashboard():
    # Get all decks of user to display it
    user_decks = UserDecks.query.filter_by(user_id=current_user.id).all()
    decks = {}
    for user_deck in user_decks:
        d = Decks.query.filter_by(deck_id=user_deck.deck_id).first()
        deck_cards = DeckCards.query.filter_by(deck_id = user_deck.deck_id).all()
        card_num = len(deck_cards)
        decks[d] = card_num
    return render_template("index.html", user=current_user, decks = decks.keys(), cards = decks) 

# ----------------------- Deck Management -----------------------------
@app.route("/add", methods=["POST"])
@login_required
def add():
    name = request.form['deck_name']
    if name is None or name == '':
        flash(message = "Name can't be empty")
        return redirect(url_for("dashboard"))
    else:
        new_deck = Decks(name=name)
        db.session.add(new_deck)
        db.session.commit()
        new_user_deck = UserDecks(user_id = current_user.id, deck_id = new_deck.deck_id)
        db.session.add(new_user_deck)
        db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/delete/<int:deck_id>")
@login_required
def delete(deck_id):
    #Delete all cards related to deck
    d = Decks.query.filter_by(deck_id=deck_id).first()
    if d is not None:
        deck_cards = DeckCards.query.filter_by(deck_id=deck_id).all()
        for deck_card in deck_cards:
            card = Cards.query.filter_by(card_id=deck_card.card_id).first()
            db.session.delete(deck_card)
            db.session.delete(card)

        #Delete all user_decks related to deck
        user_decks = UserDecks.query.filter_by(user_id = current_user.id, deck_id=deck_id).all()
        for user_deck in user_decks:
            db.session.delete(user_deck)
        db.session.delete(d)
        db.session.commit()
    else:
        flash(message = "Deck can't be found")
    return redirect(url_for("dashboard"))

@app.route("/edit/<int:deck_id>", methods=["GET", "POST"])
@login_required
def edit(deck_id):
    deck = Decks.query.filter_by(deck_id = deck_id).first()
    name = deck.name
    if request.method == "GET":
        deck_cards = DeckCards.query.filter_by(deck_id = deck_id).all()
        cards = []
        for deck_card in deck_cards:
            card = Cards.query.filter_by(card_id = deck_card.card_id).first()
            cards.append(card)
        return render_template("edit_deck.html", deck=deck, cards = cards)
    else:
        new_name = request.form['deck_name']
        if new_name is None or new_name == '':
            flash('Name must not be empty!')
            return redirect(url_for("edit", deck_id = deck_id))
        if new_name != name:
            deck.name = new_name
            db.session.commit()

    return redirect(url_for("dashboard"))
            

# ---------------------- Card Management ---------------------------
@app.route("/add_card", methods=["POST"])
@login_required
def add_card():
    ques = request.form['card_front']
    ans = request.form['card_back']
    flag = True
    if ques is None or ques == '':
        flash(message = "Question can't be empty")
        flag = False
    if ans is None or ans == '':
        flash(message = "Answer can't be empty")
        flag = False
    # Ques and ans is not empty - flag = True
    if flag:
        deck_id = request.form['deck_name']
        new_card = Cards(front = ques, back = ans, score = 0, count = 0)
        db.session.add(new_card)
        db.session.commit()
        new_deck_card = DeckCards(deck_id = deck_id, card_id = new_card.card_id)
        db.session.add(new_deck_card)
        db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/edit_card/<int:card_id>", methods=["POST"])
@login_required
def edit_card(card_id):
    card = Cards.query.filter_by(card_id = card_id).first()
    deck_card = DeckCards.query.filter_by(card_id = card_id).first()
    deck = Decks.query.filter_by(deck_id = deck_card.deck_id).first()
    front = request.form['front']
    back = request.form['back']

    if (front != '' and back != ''):
        card.front = front
        card.back = back
        db.session.commit()
    else:
        if front is None or front == '':
            flash("Question can't be empty!")
        if back is None or back == '':
            flash("Answer can't be empty!")
    return redirect(url_for("edit", deck_id = deck.deck_id))


@app.route("/delete_card/<int:card_id>")
@login_required
def delete_card(card_id):
    card = Cards.query.filter_by(card_id =card_id).first()
    if card is None:
        flash("Card not found or can't be deleted!")
        return redirect(url_for("dashboard"))
    else:
        deck_card = DeckCards.query.filter_by(card_id = card_id).first()
        if deck_card:
            db.session.delete(deck_card)
        db.session.delete(card)
        db.session.commit()
    return redirect(url_for("edit", deck_id = deck_card.deck_id))

# ------------------- Deck Review --------------------------------
@app.route("/review/<int:deck_id>", methods=["GET", "POST"])
@login_required
def review(deck_id):
    # Basic Validation
    deck = Decks.query.filter_by(deck_id = deck_id).first()
    if deck is None:
        flash("Deck can't be found!")
        return redirect(url_for("dashboard"))
    deck_cards = DeckCards.query.filter_by(deck_id = deck_id).all()

    if len(deck_cards) == 0:
        flash("No cards in the deck!")
        return redirect(url_for("dashboard"))
    cards = []

    # Check which cards need to be reviewed
    card_count = 0
    for deck_card in deck_cards:
        card = Cards.query.filter_by(card_id = deck_card.card_id).first()
        card_count += 1
        if card.score < 18:
            cards.append(card)
    
    if request.method == "GET":
        cur_card = -1
        if not cards:
            sum_count = 0
            count = 0
            for deck_card in deck_cards:
                mod_card = Cards.query.filter_by(card_id = deck_card.card_id).first()
                mod_card.score = 0
                sum_count += mod_card.count
                mod_card.count = 0
                count += 1
            avg_count = sum_count // count
            deck.score = avg_count
            deck.last_reviewed = datetime.datetime.now()
            db.session.commit()
        else:
            cur_card = cards[randint(0, len(cards) - 1)]
        return render_template("review.html", deck = deck, card = cur_card, cards=cards, num_cards = card_count)
    
    # POST
    else:
        eval = request.form['eval']
        card_id = request.form['card_id']
        card = Cards.query.filter_by(card_id = card_id).first()
        if eval == "easy":
            card.score = card.score + 9
        elif eval == "medium":
            card.score = card.score + 6
        else:
            card.score = card.score + 3
        card.count = card.count + 1 
        db.session.commit()
        return redirect(url_for("review", deck_id = deck_id, cards=cards, num_cards=card_count))

