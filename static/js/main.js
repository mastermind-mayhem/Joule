function navigate(path) {
    window.location.href = path;
}

async function setMeal(day, meal, recipeId) {
    try {
        const response = await fetch("/api/set-meal", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                day: day,
                meal: meal,
                recipe_id: recipeId || null
            })
        });
        
        if (response.ok) {
            console.log('Meal updated successfully');
        }
    } catch (error) {
        console.error('Error updating meal:', error);
        alert('Failed to update meal. Please try again.');
    }
}

async function addRecipe() {
    const name = document.getElementById('recipe-name').value.trim();
    const ingredientsText = document.getElementById('recipe-ingredients').value.trim();
    const instructions = document.getElementById('recipe-instructions').value.trim();
    
    if (!name || !ingredientsText || !instructions) {
        alert('Please fill in all fields');
        return;
    }
    
    // Parse ingredients
    const ingredients = [];
    const lines = ingredientsText.split('\n');
    for (const line of lines) {
        if (line.trim()) {
            const parts = line.split(',').map(p => p.trim());
            if (parts.length >= 2) {
                ingredients.push([parts[0], parts.slice(1).join(', ')]);
            }
        }
    }
    
    if (ingredients.length === 0) {
        alert('Please add at least one ingredient in the format: item, quantity');
        return;
    }
    
    try {
        const response = await fetch("/api/add-recipe", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: name,
                instructions: instructions,
                ingredients: ingredients
            })
        });
        
        if (response.ok) {
            alert('Recipe added successfully!');
            window.location.reload();
        }
    } catch (error) {
        console.error('Error adding recipe:', error);
        alert('Failed to add recipe. Please try again.');
    }
}

function toggleMenu() {
    const navLinks = document.getElementById('navLinks');
    navLinks.classList.toggle('active');
}

// Close menu when clicking outside
document.addEventListener('click', function(event) {
    const nav = document.querySelector('.nav-content');
    const navLinks = document.getElementById('navLinks');
    
    if (navLinks && !nav.contains(event.target)) {
        navLinks.classList.remove('active');
    }
});

// Close menu when clicking a link
document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', function() {
        document.getElementById('navLinks').classList.remove('active');
    });
});