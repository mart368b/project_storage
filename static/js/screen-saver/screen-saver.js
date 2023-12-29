
/*
Simple 2D JavaScript Vector Class
from evanw's lightgl.js
https://github.com/evanw/lightgl.js/blob/master/src/vector.js
*/

function Vector(x, y) {
    this.x = x || 0;
    this.y = y || 0;
}

/* INSTANCE METHODS */

Vector.prototype = {
    negative: function() {
        this.x = -this.x;
        this.y = -this.y;
        return this;
    },
    add: function(v) {
        this.x += v.x;
        this.y += v.y;
        return this;
    },
    subtract: function(v) {
        this.x -= v.x;
        this.y -= v.y;
        return this;
    },
    multiply: function(v) {
        if (v instanceof Vector) {
            this.x *= v.x;
            this.y *= v.y;
        } else {
            this.x *= v;
            this.y *= v;
        }
        return this;
    },
    divide: function(v) {
        if (v instanceof Vector) {
            if(v.x != 0) this.x /= v.x;
            if(v.y != 0) this.y /= v.y;
        } else {
            if(v != 0) {
                this.x /= v;
                this.y /= v;
            }
        }
        return this;
    },
    equals: function(v) {
        return this.x == v.x && this.y == v.y;
    },
    dot: function(v) {
        return this.x * v.x + this.y * v.y;
    },
    cross: function(v) {
        return this.x * v.y - this.y * v.x
    },
    length: function() {
        return Math.sqrt(this.dot(this));
    },
    normalize: function() {
        return this.divide(this.length());
    },
    min: function() {
        return Math.min(this.x, this.y);
    },
    max: function() {
        return Math.max(this.x, this.y);
    },
    toAngles: function() {
        return -Math.atan2(-this.y, this.x);
    },
    angleTo: function(a) {
        return Math.acos(this.dot(a) / (this.length() * a.length()));
    },
    toArray: function(n) {
        return [this.x, this.y].slice(0, n || 2);
    },
    clone: function() {
        return new Vector(this.x, this.y);
    },
    setMag: function(m){
        return this.normalize().multiply(m);
    },
    set: function(x, y) {
        this.x = x; this.y = y;
        return this;
    },
    limit: function(limit, lower){
        let l = this.length();
        if ( l > limit){
            this.divide(l).multiply(limit);
            return this;
        }
        if (lower != null){
            if (l < lower){
                this.divide(l).multiply(lower);
                return this;
            }
        }
        return this;
    },
    distance: function(a, b){
        return Math.sqrt(Math.pow(b.x - a.x, 2) + Math.pow(b.y - a.y, 2))
    },
    drawPoint: function(){
        if (this.g == null){
            this.g = new Graphics();
            app.stage.addChild(this.g);
        }else{
            this.g.clear();
        }
        this.g.lineStyle(1,0xff0000, 2);
        this.g.drawCircle(this.x, this.y, 10);
    }
};

/* STATIC METHODS */
Vector.negative = function(v) {
    return new Vector(-v.x, -v.y);
};
Vector.add = function(a, b) {
    if (b instanceof Vector) return new Vector(a.x + b.x, a.y + b.y);
    else return new Vector(a.x + b, a.y + b);
};
Vector.subtract = function(a, b) {
    return new Vector(a.x - b.x, a.y - b.y);
};
Vector.multiply = function(a, b) {
    if (b instanceof Vector) return new Vector(a.x * b.x, a.y * b.y);
    else return new Vector(a.x * b, a.y * b);
};
Vector.divide = function(a, b) {
    if (b instanceof Vector) return new Vector(a.x / b.x, a.y / b.y);
    else return new Vector(a.x / b, a.y / b);
};
Vector.equals = function(a, b) {
    return a.x == b.x && a.y == b.y;
};
Vector.dot = function(a, b) {
    return a.x * b.x + a.y * b.y;
};
Vector.cross = function(a, b) {
    return a.x * b.y - a.y * b.x;
};

var UNITVECTOR = new Vector();

function lineTo(ctx, p0, p1, color) {
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.moveTo(p0.x,p0.y);
    ctx.lineTo(p1.x,p1.y);
    ctx.stroke();
}

function linesTo(ctx, points, color) {
    ctx.beginPath();
    ctx.strokeStyle = color;
    
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
        if (points[i] == null) {
            i++;
            ctx.moveTo(points[i].x, points[i].y);
        } else {
            ctx.lineTo(points[i].x, points[i].y);
        }
    }
    ctx.stroke();
}

let auto_reset_box = document.getElementById("auto_reset_box");
let rotation_vel_varience_slider = document.getElementById("rotation_vel_varience");
let speed_varience_slider = document.getElementById("speed_varience_slider");
let step_size_slider = document.getElementById("step_size_slider");
let particle_count_slider = document.getElementById("particle_count_slider");
let start_radius_slider = document.getElementById("start_radius_slider");

var c = document.getElementById("myCanvas");
var ctx = c.getContext("2d");

let canvas_bounds = c.getBoundingClientRect()
c.width = canvas_bounds.width;
c.height = canvas_bounds.height;

class Particle {
    constructor(x, y, color) {
        this.p = new Vector(x, y);
        this.rotation = Math.random() * Math.PI * 2.0;
        this.rotation_vel = 0.1;
        this.rotation_vel_varience = rotation_vel_varience_slider.value * (2.0*Math.PI/100.0);
        this.speed = 2.0;
        this.speed_varience = speed_varience_slider.value;
        this.color = color
        this.points = []
    }

    update() {
        this.rotation += this.rotation_vel * Math.random() * this.rotation_vel_varience * Math.sign(Math.random() - 0.5);
        let vel = new Vector(Math.sin(this.rotation), Math.cos(this.rotation)).normalize().multiply(this.speed * Math.random() * this.speed_varience);
        let new_p = Vector.add(this.p, vel);
        this.points.push(this.p);
        this.p = new_p;

        if (this.p.x > c.width) {
            this.push_jump();
            this.p.x = 0.0;
        }

        if (this.p.x < 0.0) {
            this.push_jump();
            this.p.x = c.width;
        }

        if (this.p.y > c.height) {
            this.push_jump();
            this.p.y = 0.0;
        }

        if (this.p.y < 0.0) {
            this.push_jump();
            this.p.y = c.height;
        }
    }

    push_jump() {
        if (this.points.length == 0) {
            this.points.push(null);
            return;
        }
        if (this.points[this.points.length - 1] == null) {
            return;
        }

        this.points.push(null);
    }

    draw() {
        this.points.push(this.p);
        linesTo(ctx, this.points, this.color);
        this.points = []
    }
}

colors = [
    "#73b5d6",
    "#7a95d3",
    "#7b75d1",
    "#a36fce",
    "#b36acc",
    "#b12ccc",
    "#8522cc",
    "#6826cc",
    "#4f33cc",
    "#3349cc",
    "#266ecc",
    "#2c96cc",
    "#59a7cc",
    "#CC7A9D",
    "#CC4D9D",
    "#CC1096",
    "#CC005B",
    "#CC0619",
    "#CC2504",
    "#CC7428",
    "#CC8F59",
    "#CC6155",
    "#CC5B77",
    "#CC74AA"
]
let particles = [];

function spawn_particles() {
    particles = []

    let particle_count = particle_count_slider.value
    let steps = Math.PI*2 / particle_count
    let radius = start_radius_slider.value

    for (let i = 0; i < particle_count; i++) {

        let x = Math.sin(steps * i) * radius + c.width / 2.;
        let y = Math.cos(steps * i) * radius + c.height / 2.;

        if (x < 0 || x > c.width || y < 0 || y > c.height) {
            continue;
        }

        let p = new Particle(
            x,
            y,
            colors[i % colors.length]
        );
        
        particles.push(p)
    }
}

spawn_particles();

setInterval(() => {
    let step_count = Math.ceil(step_size_slider.value)
    for (let i = 0; i < particles.length; i++) {
        for (let step = 0; step < step_count; step++) {
            particles[i].update();
        }

        particles[i].draw()
    }
}, 10);

function clearScreen() {
    ctx.clearRect(0, 0, c.width, c.height);
    spawn_particles();
}

rotation_vel_varience_slider.oninput = function() {
    for (let p of particles) {
        p.rotation_vel_varience = this.value * ((2.0 * Math.PI) / 100.0);
    }

    if (auto_reset_box.checked) {
        clearScreen();
    }
};

speed_varience_slider.oninput = function() {
    for (let p of particles) {
        p.speed_varience = this.value;
    }

    if (auto_reset_box.checked) {
        clearScreen();
    }
};

step_size_slider.oninput = function() {
    if (auto_reset_box.checked) {
        clearScreen();
    }
};

particle_count_slider.oninput = function()  {
    if (auto_reset_box.checked) {
        clearScreen();
    }
};

start_radius_slider.oninput = function() {
    if (auto_reset_box.checked) {
        clearScreen();
    }
};

document.getElementsByTagName("BODY")[0].onresize = function() {
    let canvas_bounds = c.getBoundingClientRect()
    c.width = canvas_bounds.width;
    c.height = canvas_bounds.height;
}

let reset_button = document.getElementById("reset");
reset_button.onclick = clearScreen;
