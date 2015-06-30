if [[ "$1" == 1 ]]; then
  PYTHONPATH=${PYTHONPATH}:./python python make_shape.py -s arc -p 4.55 3.9 -n 16 -l 2 -a 135 -b 315 -r 5.5 4.8 66 55 57 13 14 15 58 27 60 28 65 32 53 12 3 51
fi

if [[ "$1" == 2 ]]; then
    PYTHONPATH=${PYTHONPATH}:./python python make_shape.py -s triangle -p 1.75 1.4 -l 1.0 -r 5.5 4.8 -n 3 32 65 28
fi

if [[ "$1" == 3 ]]; then
    PYTHONPATH=${PYTHONPATH}:./python python make_shape.py -s arc -p 2 4  -n 9 -l 1 -a 0 -b 320 -r 5.5 4.8 66 55 57 13 14 15 58 27 60
fi

if [[ "$1" == 4 ]]; then
    PYTHONPATH=${PYTHONPATH}:./python python make_shape.py -s square -p 5.4 0.55 -l 1.0 -r 5.5 4.8 -n 4 12 51 53 3
fi

