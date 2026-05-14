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
### Telemetry Pipeline
In order to get telemetry data from Assetto Corsa, data must be passed from the games Python API through an app run in the game or with the games shared memory files. 

### Assetto Corsa Environment
The files that control an Assetto Corsa instance and the Gymnasium environment can be found in the assetto_corsa folder. 

- Observation
- Action
- Reward

### Assetto Corsa Python Application
### Parallel Environments Support

In short, to get parallel environments working, copy version_original.dll and version.dll into your Assetto Corsa folder in your Steam library. The DLLs are located in the shared_memory_proxy folder. Also, instances need to be started serially as they all need to read from the same config files. 

Assetto Corsa is a rather lightweight games (especially when lowering the resolution) using current hardware as the game is over 10 years old now. It also allows you to open up multiple races concurrently with the executable acs.exe. This made it a good candidate for a autonomous racing environment as I thought it would be easy to have parallel environments. However, getting data from each individual instance caused some trouble.  This is because the Assetto Corsa Python API doesn't contain all the data required for observation, such as the cars heading, so we must get the remaining telemetry data from the shared memory file. This causes a problem since each instance has a fixed filename for the shared memory file. So each instance rewrites the same file, leading to possibly receiving data from a different instance.

So in order to use parallel environments, either multiple systems need to be used or the shared memory files need to be renamed. Since I didn't have access to multiple machines and multiple copies of the game, I went with the latter. To change the names of the shared memory files, I created a DLL proxy to intercept Windows system calls to create and open files, then add a suffix to the filename based on which instance the game is. The implementation and DLLs can be found in the shared_memory_proxy folder. 

I was able to train an agent using 6 parallel environments on a single system with an Nvidia RTX 3080 and Intel 12700k. So having access to parallel environments can really speed up training since the environment updates are capped at 30hz. 

## Prerequisites
- Python version 3.14
- [Assetto Corsa](https://store.steampowered.com/app/244210/Assetto_Corsa/) 
- [Content Manager (AC mod)](https://assettocorsa.club/content-manager.html)
- [Custom Shaders Patch (AC  mod)](https://acstuff.club/patch/)
- [vJoy](https://sourceforge.net/projects/vjoystick/)

## Installation


## Usage
