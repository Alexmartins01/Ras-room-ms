#!/bin/bash

gunicorn -w 4 'rooms:create_app()'