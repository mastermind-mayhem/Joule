# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
from contextlib import closing
import os

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['DATABASE'] = os.path.join(BASE_DIR, 'data', 'meal_planner.db')

def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_db()) as db:
        # remove the script to refresh the database when implemented
        # DROP TABLE IF EXISTS recipes;
        # DROP TABLE IF EXISTS ingredients;
        # DROP TABLE IF EXISTS meal_plan;
        db.executescript('''

            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                instructions TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS  ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                item TEXT NOT NULL,
                quantity TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS  meal_plan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_index INTEGER NOT NULL,
                meal TEXT NOT NULL,
                recipe_id INTEGER NOT NULL,
                UNIQUE(day_index, meal),
                FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
            );
        ''')
        
        db.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recipes')
def recipes():
    with closing(get_db()) as db:
        recipes = db.execute('SELECT * FROM recipes ORDER BY name').fetchall()
        recipe_list = []
        for recipe in recipes:
            ingredients = db.execute('SELECT item, quantity FROM ingredients WHERE recipe_id = ?', (recipe['id'],)).fetchall()
            recipe_list.append({
                'id': recipe['id'],
                'name': recipe['name'],
                'instructions': recipe['instructions'],
                'ingredients': ingredients
            })
    return render_template('recipes.html', recipes=recipe_list)

@app.route('/meal-plan')
def meal_plan():
    with closing(get_db()) as db:
        recipes = db.execute('SELECT * FROM recipes ORDER BY name').fetchall()
        plan_rows = db.execute('SELECT day_index, meal, recipe_id FROM meal_plan').fetchall()
        
        plan = {}
        for row in plan_rows:
            plan[(row['day_index'], row['meal'])] = row['recipe_id']
    
    days = [(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), 
            (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')]
    meals = ['breakfast', 'lunch', 'dinner']
    
    return render_template('meal_plan.html', recipes=recipes, plan=plan, days=days, meals=meals)

@app.route('/grocery-list')
def grocery_list():
    with closing(get_db()) as db:
        # Get all recipes in the meal plan
        plan_recipes = db.execute('''
            SELECT DISTINCT recipe_id FROM meal_plan
        ''').fetchall()
        
        grocery = {}
        for row in plan_recipes:
            ingredients = db.execute('''
                SELECT item, quantity FROM ingredients WHERE recipe_id = ?
            ''', (row['recipe_id'],)).fetchall()
            
            for ing in ingredients:
                item = ing['item']
                qty = ing['quantity']
                if item not in grocery:
                    grocery[item] = []
                grocery[item].append(qty)
    
    return render_template('grocery.html', grocery=grocery)

@app.route('/api/set-meal', methods=['POST'])
def set_meal():
    data = request.json
    day = data['day']
    meal = data['meal']
    recipe_id = data.get('recipe_id')
    
    with closing(get_db()) as db:
        # Delete existing meal plan entry
        db.execute('DELETE FROM meal_plan WHERE day_index = ? AND meal = ?', (day, meal))
        
        # Insert new meal plan entry if recipe_id is provided
        if recipe_id:
            db.execute('INSERT INTO meal_plan (day_index, meal, recipe_id) VALUES (?, ?, ?)', 
                      (day, meal, recipe_id))
        
        db.commit()
    
    return jsonify({'success': True})

@app.route('/api/add-recipe', methods=['POST'])
def add_recipe():
    data = request.json
    name = data['name']
    instructions = data['instructions']
    ingredients = data['ingredients']  # List of [item, quantity] pairs
    
    with closing(get_db()) as db:
        cursor = db.execute('INSERT INTO recipes (name, instructions) VALUES (?, ?)', 
                           (name, instructions))
        recipe_id = cursor.lastrowid
        
        for item, qty in ingredients:
            db.execute('INSERT INTO ingredients (recipe_id, item, quantity) VALUES (?, ?, ?)', 
                      (recipe_id, item, qty))
        
        db.commit()
    
    return jsonify({'success': True, 'recipe_id': recipe_id})

@app.route('/api/delete-recipe/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    with closing(get_db()) as db:
        db.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
        db.commit()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)