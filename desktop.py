"""Ponto de entrada do executável Windows e do ensaio de distribuição."""
import sys

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--self-test":
        from punching.distribution_check import run
        raise SystemExit(run(sys.argv[2]))
    from Punching_EC2_GUI import main
    main()
