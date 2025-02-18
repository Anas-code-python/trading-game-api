from flask import Flask, jsonify, request
import random
import threading
import time

app = Flask(__name__)

class Player:
    def __init__(self, name, number):
        self.name = name
        self.number = number  # Sealed number
        self.balance = 1000  # Starting money
        self.positions = []  # List of active trades

    def buy(self, price, quantity):
        cost = price * quantity
        if self.balance >= cost:
            self.positions.append(("buy", price, quantity))
            self.balance -= cost
            return True
        return False

    def sell(self, price, quantity):
        self.positions.append(("sell", price, quantity))
        self.balance += price * quantity
        return True

    def unwind_positions(self, current_price):
        profit_loss = 0
        for pos in self.positions:
            action, price, quantity = pos
            if action == "buy":
                profit_loss += (current_price - price) * quantity
            else:
                profit_loss += (price - current_price) * quantity

        self.balance += profit_loss
        self.positions = []  # Clear positions
        return profit_loss

class TradingGame:
    def __init__(self, num_players=9, number_range=10):
        self.num_players = num_players
        self.number_range = number_range
        self.players = [Player(f"Player {i+1}", random.randint(1, self.number_range)) for i in range(self.num_players)]
        self.hidden_number = random.randint(1, self.number_range)
        self.trading_prices = []
        self.last_trade_price = random.randint(10, 50)  # Starting market price
        self.trading_session_active = False

    def match_trade(self, buyer_name, seller_name, price, quantity):
        buyer = next((p for p in self.players if p.name == buyer_name), None)
        seller = next((p for p in self.players if p.name == seller_name), None)

        if buyer and seller and buyer.buy(price, quantity) and seller.sell(price, quantity):
            self.trading_prices.append(price)
            self.last_trade_price = price
            return {"message": f"Trade matched: {buyer_name} bought from {seller_name} at {price} for {quantity} contracts."}
        return {"error": "Trade failed. Check balance or players."}

    def settle_trades(self):
        final_price = sum(player.number for player in self.players)
        results = {
            "final_price": final_price,
            "players": [{ "name": p.name, "balance": p.balance, "profit_loss": p.unwind_positions(final_price) } for p in self.players]
        }
        return results

    def get_market_state(self):
        return {
            "last_trade_price": self.last_trade_price,
            "players": [{ "name": p.name, "balance": p.balance, "positions": p.positions } for p in self.players]
        }

game = TradingGame()

@app.route('/start_game', methods=['POST'])
def start_game():
    global game
    game = TradingGame()
    game.trading_session_active = True
    return jsonify({"message": "Trading session started!"})

@app.route('/game_state', methods=['GET'])
def game_state():
    return jsonify(game.get_market_state())

@app.route('/trade', methods=['POST'])
def trade():
    data = request.json
    buyer_name = data.get("buyer")
    seller_name = data.get("seller")
    price = data.get("price")
    quantity = data.get("quantity")

    if not all([buyer_name, seller_name, price, quantity]):
        return jsonify({"error": "Missing parameters!"}), 400

    result = game.match_trade(buyer_name, seller_name, price, quantity)
    return jsonify(result)

@app.route('/end_game', methods=['POST'])
def end_game():
    game.trading_session_active = False
    results = game.settle_trades()
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
