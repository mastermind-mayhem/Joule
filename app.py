# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
from contextlib import closing

app = Flask(__name__)
app.config['DATABASE'] = './data/meal_planner.db'

def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_db()) as db:
        # remove the script to refresh the database when implemented
        db.executescript('''
            DROP TABLE IF EXISTS recipes;
            DROP TABLE IF EXISTS ingredients;
            DROP TABLE IF EXISTS meal_plan;
            
            CREATE TABLE recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                instructions TEXT NOT NULL
            );
            
            CREATE TABLE ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                item TEXT NOT NULL,
                quantity TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
            );
            
            CREATE TABLE meal_plan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_index INTEGER NOT NULL,
                meal TEXT NOT NULL,
                recipe_id INTEGER NOT NULL,
                UNIQUE(day_index, meal),
                FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
            );
        ''')
        
        # Insert sample recipes
        sample_recipes = [
            ('Caesar Salad', 'Wash and chop romaine lettuce. Toss with Caesar dressing. Top with grated parmesan and croutons. Serve immediately.',
             [('romaine lettuce', '1 head'), ('caesar dressing', '1/2 cup'), ('parmesan cheese', '1/4 cup'), ('croutons', '1 cup')]),
            ('Spaghetti Bolognese', 'Cook spaghetti according to package directions. Brown ground beef in large pan. Add tomato sauce, herbs, and simmer 20 minutes. Serve sauce over pasta.',
             [('spaghetti', '400g'), ('ground beef', '500g'), ('tomato sauce', '2 cups'), ('onion', '1'), ('italian herbs', '2 tsp')]),
            ('Oatmeal', 'Bring water to boil. Add oats and reduce heat. Simmer 5 minutes, stirring occasionally. Top with honey and berries.',
             [('oats', '1 cup'), ('water', '2 cups'), ('honey', '1 tbsp'), ('mixed berries', '1/2 cup')]),
            ('Turkey Sandwich', 'Toast bread if desired. Layer turkey, cheese, lettuce, and tomato. Spread mayo on bread. Assemble sandwich.',
             [('bread', '2 slices'), ('turkey', '4 slices'), ('cheese', '2 slices'), ('lettuce', '2 leaves'), ('tomato', '2 slices'), ('mayonnaise', '1 tbsp')])
        ]
        
        for name, instructions, ingredients in sample_recipes:
            cursor = db.execute('INSERT INTO recipes (name, instructions) VALUES (?, ?)', (name, instructions))
            recipe_id = cursor.lastrowid
            for item, qty in ingredients:
                db.execute('INSERT INTO ingredients (recipe_id, item, quantity) VALUES (?, ?, ?)', (recipe_id, item, qty))
        
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

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)