# Gambling App

## Overview

Welcome to the Gambling Simulation System! At first glance, this might look like a simple casino game, but under the hood, it is a robust, enterprise-grade backend application built entirely from scratch using Python and MySQL.

The core idea behind this project is to simulate a "Calculative Gambler". Instead of just randomly betting until a player goes broke, this system forces discipline. A player sits at the table with strict rules: an initial bankroll, a "Win Target" (when to walk away happy), and a "Loss Stop" (when to cut their losses). The system actively monitors their money and automatically ends the session the moment they hit their boundaries.

This project was built to demonstrate advanced software engineering principles, including ACID database transactions, row-level locking, Object-Oriented Programming (OOP), and clean Separation of Concerns (SoC).

---

### Key Features
The system is divided into 7 core modules (Use Cases):

Player Profiles: Create and manage user accounts, setting their personal betting preferences, minimum stakes, and global win/loss thresholds.

Bank-Grade Ledger: Every single cent that moves (deposits, bets, winnings, losses) is recorded in an immutable transaction table. No money can simply "disappear."

Smart Betting Mechanism: Place bets using different mathematical strategies (like Fixed or Martingale). The system handles the probability logic and calculates payouts.

Session Guardian: The app acts as a strict casino dealer. If a player hits their predetermined win limit or loss limit, the system instantly auto-ends their session to protect their bankroll.

Deep Analytics: Automatically calculates advanced metrics after every game, including Win Rates, Return on Investment (ROI), Profit Factors, and Longest Streaks.

Bulletproof Validation: A custom security layer that intercepts bad user inputs (like trying to bet negative money or betting more than they have) before it ever touches the database.

Interactive Casino Table: A rich, interactive Command Line Interface (CLI) dashboard that lets users sit at a virtual table, place bets, pause their sessions, and view real-time stats.

---

### Tech Stack & Architecture

Language: Python

Database: MySQL

Libraries: mysql-connector-python (for DB connections), python-dotenv (for secure environment variables).

Architecture Highlights: * No ORMs: All database interactions are written in raw, optimized SQL.

ACID Transactions & Locking: Uses START TRANSACTION and FOR UPDATE (pessimistic locking) to ensure money isn't double-spent if two requests happen at the exact same time.

Modular Design: The code is strictly split into models, services, utils, reports, and ui. The UI never talks to the database directly—it only communicates through the services.
