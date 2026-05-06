# Assetto Corsa RL

## Overview
This project implements a reinforcement learning (RL) system for autonomous racing in Assetto Corsa (AC). The goal is to train an agent to drive competitively by learning control policies directly from interaction with Assetto Corsa.

The environment is built around a custom telemetry pipeline that streams real-time vehicle state from an Assetto Corsa instance into a Python-based RL framework. Observations include vehicle dynamics (e.g., velocity, acceleration, steering inputs) and a forward-looking track representation defined by a corridor of points relative to the car. This allows the agent to reason about both its current state and the geometry of the track ahead. To improve sample efficiency and training speed, multiple game instances can be run in parallel, enabling the agent to collect experience from several environments simultaneously. Parallel instances are run on a single machine.

I have implemented an agent using the Soft Actor-Critic (SAC) algorithm, which is well suited for continuous control tasks such as throttle, brake, and steering. 

## Features
- Real-time RL training
- Parallel environments
- Custom telemetry pipeline
- etc.

## System Architecture
### Assetto Corsa Environment
### Assetto Corsa Python Application
### Parallel Environments Support

## Prerequisites
- Python version 3.14
- [Assetto Corsa](https://store.steampowered.com/app/244210/Assetto_Corsa/) 
- [Content Manager (AC mod)](https://assettocorsa.club/content-manager.html)
- [Custom Shaders Patch (AC  mod)](https://acstuff.club/patch/)
- [vJoy](https://sourceforge.net/projects/vjoystick/)

## Installation
- Clone repo
- Install dependencies
- Build components

## Usage
- How to start training
- How to run evaluation