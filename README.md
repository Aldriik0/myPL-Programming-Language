# Presentation
[Presentation](https://youtu.be/fFY9hZQD-8Y)

# Pre-requisites/Dependencies
To run the _optional_ rust translator feature you must download the Rust compiler.
### Unix Machines (Mac, Linux)
```curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh```
### Windows
Follow the directions on the [Official Rust Site](https://www.rust-lang.org/tools/install)
# How To Run
There is are multiple ways to run the myPL compiler that vary on the machine that you are using
### Unix Machines
For Unix-based machines (Mac and Linux), you can use one of the following two ways to compile and run
the myPL compiler


```./mypl <flag> <file>```


or


```python3 mypl.py <flag> <file>```

For more information on each flag and their roles run the following


```./mypl --help``` 

or 

```./mypl -h```
### Windows Users
For Windows-based machines, you can use one of the following two ways to compile and run the myPL
compiler.

```.\mypl.bat <flag> <file>```

or

```python mypl.py <flag> <file>```

For more information on each flag and their roles, run the following

```.\mypl.bat --help``` 

or

```.\mypl.bat -h```


## Running the Rust Transcompiler
To run the rust transcompiler you must add the ```--rust``` flag to your appropriate compile
command. After this you then need to run the following regardless of the machine:

```rustc exec.rs -o exec```

Then run

```./exec```