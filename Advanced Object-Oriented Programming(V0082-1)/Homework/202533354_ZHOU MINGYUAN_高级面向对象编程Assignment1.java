package com.ajou.exercise;

import java.util.*;
import java.util.regex.*;

public class Main {

    private static final Scanner sc = new Scanner(System.in);
    private static final Pattern SENTENCE_PATTERN = Pattern.compile("^[A-Za-z0-9 ,;:'\"-]+[.!?]$");
    private static final Pattern BAD_WORD = Pattern.compile(".*[\\p{Punct}0-9].*");
    private static final Set<String> WORDBOOK = new TreeSet<>();

    private static String readSentence() {
        String s;
        while (true) {
            System.out.println("Please enter a sentence ending with . or ! or ?: ");
            s = sc.nextLine().trim();
            if (s.isEmpty()) {
                System.out.println("句子不能为空，请重新输入。");
                continue;
            }
            if (!SENTENCE_PATTERN.matcher(s).matches()) {
                System.out.println("输入非法或缺少句末符，请重新输入。");
                continue;
            }
            if (!s.matches(".*[A-Za-z].*")) {
                System.out.println("句中必须包含至少一个字母，请重新输入。");
                continue;
            }
            break;
        }
        return s.toLowerCase();
    }

    private static void buildWordBook() {
        String s = readSentence();
        String[] words = s.split("[.!?,\\s]+");
        for (String w : words) {
            if (!w.isEmpty() && !BAD_WORD.matcher(w).matches()) {
                WORDBOOK.add(w);
            }
        }
    }

    private static void printHangman(int wrong) {
        System.out.println();
        String[] base = {
                " ----- ",
                "|     |",
                "|      ",
                "|        ",
                "|      ",
                "|       ",
                "|        ",
        };

        char[][] canvas = new char[base.length][];
        for (int i = 0; i < base.length; i++) {
            canvas[i] = base[i].toCharArray();
        }

        int col = canvas[0].length - 1;

        if (wrong >= 1) {
            canvas[2][col] = 'o';
        }
        if (wrong >= 2) {
            canvas[3][col] = '|';
        }
        if (wrong >= 3) {
            canvas[4][col] = '|';
        }
        if (wrong >= 4) {
            canvas[3][col - 1] = '-';
        }
        if (wrong >= 5) {
            canvas[3][col - 2] = '-';
        }
        if (wrong >= 6) {
            canvas[3][col + 1] = '-';
        }
        if (wrong >= 7) {
            canvas[3][col + 2] = '-';
        }
        if (wrong >= 8) {
            canvas[5][col - 1] = '/';
        }
        if (wrong >= 9) {
            canvas[6][col - 2] = '/';
        }
        if (wrong >= 10) {
            canvas[5][col + 1] = '\\';
        }
        if (wrong == 11) {
            canvas[6][col + 2] = '\\';
        }

        for (char[] line : canvas) {
            System.out.println(new String(line));
        }
        System.out.println();
    }


    private static void guessWord() {
        String word = new ArrayList<>(WORDBOOK).get(new Random().nextInt(WORDBOOK.size()));
        String guess = String.join(" ", word.split("")).toUpperCase();
        int len = word.length();
        System.out.println("YOU WILL GUESS A WORD WITH " + len + " LETTERS!");
        int count = 0;
        boolean found = false;
        StringBuilder guessed = new StringBuilder();
        StringBuilder curGuess = new StringBuilder("_".repeat(len));
        while (count < 12) {
            printHangman(count);
            System.out.println("Letters already guessed: " + String.join(" ", guessed.toString().split("")));
            System.out.println("The current state of your guess: " + String.join(" ", curGuess.toString().split("")));
            boolean valid = false;
            String letter = "";
            while (!valid) {
                System.out.print("What is your next letter? (or type your guess) :");
                letter = sc.nextLine().trim().toLowerCase();
                if (!letter.matches("^[a-z]$")) {
                    System.out.println("Your letter is invalid!");
                } else {
                    if (guessed.indexOf(letter.toUpperCase()) != -1) {
                        System.out.println("You have already guessed the letter!");
                    } else {
                        valid = true;
                    }
                }
            }
            guessed.append(letter.toUpperCase());
            if (word.contains(letter)) {
                char chLetter = letter.charAt(0);
                for (int i = 0; i < len; i++) {
                    if (word.charAt(i) == chLetter) {
                        curGuess.setCharAt(i, chLetter);
                    }
                }
                long letterCount = word.chars().filter(ch -> ch == chLetter).count();
                System.out.println("There" + (letterCount > 1 ? " are " : " is ") + letterCount + " " + letter.toUpperCase() + "!");
            } else {
                System.out.println("There is 0 " + letter.toUpperCase() + "!");
                count++;
            }
            if (curGuess.toString().equals(word)) {
                found = true;
                break;
            }
        }
        System.out.println();
        if (found) {
            System.out.println("Congratulations, you win!");
        } else {
            System.out.println("Sorry, you lose!");
        }
        System.out.print("The word was " + guess);
    }

    private static void startGame() {
        while (true) {
            System.out.println("Welcome to the “Guess the Word” game! Ready to test your vocabulary and luck?");
            System.out.println("""
                    The game introductions are following:
                        The system will randomly choose a hidden English word.
                        You can’t see the word.
                        You guess letters to reveal the word.
                        Each wrong guess adds one step to the hanging figure.
                        If you find all letters before the figure is fully hanged, you win; otherwise you lose.""");
            System.out.println("""
                    The simple How-to-Play guides are following:
                        1. Enter a letter to start guessing.
                        2. If the letter is correct, it appears in the word.
                        3. If it’s wrong, the hangman gets closer to being hanged.
                        4. Finish the word before the hangman is complete.
                        5. Good luck!""");
            System.out.println("===================================");
            System.out.println("                Menu               ");
            System.out.println("===================================");
            System.out.println("1. View the wordbook");
            System.out.println("2. Start the game");
            System.out.println("3. Exit the game");
            System.out.print("Please enter your choice: ");

            String choice = sc.nextLine();
            switch (choice) {
                case "1":
                    System.out.println("The wordbook: " + String.join(", ", WORDBOOK));
                    System.out.print("Please press any key to return: ");
                    sc.nextLine();
                    break;

                case "2":
                    guessWord();
                    break;

                case "3":
                    System.exit(0);
                    break;

                default:
                    System.out.println("Invalid option, please re-enter.");
            }
            System.out.println();
        }
    }

    public static void main(String[] args) {
        buildWordBook();
        startGame();
    }
}