import os
import string
import io
import sys
import trace


class KeywordProcessor(object):
    """KeywordProcessor
    Note:
        * Based on Flashtext <https://github.com/vi3k6i5/flashtext>
        * loosely based on `Aho-Corasick algorithm <https://en.wikipedia.org/wiki/Aho%E2%80%93Corasick_algorithm>`.
    """

    def __init__(self, case_sensitive=False):
        """
        Args:
            case_sensitive (boolean): Keyword search should be case sensitive set or not.
                Defaults to False
        """
        self._keyword = '_keyword_'
        self.non_word_boundaries = set(string.digits + string.ascii_letters + '_')
        self.keyword_trie_dict = dict()
        self.case_sensitive = case_sensitive

    def __setitem__(self, keyword, clean_name, punctuation=None):
        """To add keyword to the dictionary
        pass the keyword and the clean name it maps to.
        Args:
            keyword : string
                keyword that you want to identify
            clean_name : string
                clean term for that keyword that you would want to get back in return or replace
                if not provided, keyword will be used as the clean name also.
            puctuation : list[char]
                list of punctuation characters to add to the keyword before adding.
        """
        if punctuation is None:
            punctuation = ['']
        status = False

        if keyword and clean_name:
            if not self.case_sensitive:
                keyword = keyword.lower()
            current_dict = self.keyword_trie_dict
            for letter in keyword:
                current_dict = current_dict.setdefault(letter, {})
            for punc in punctuation:
                if len(punc) > 0:
                    final_dict = current_dict.setdefault(punc, {})
                else:
                    final_dict = current_dict
                final_dict[self._keyword] = clean_name + punc
            status = True
        return status

    def add_keyword(self, keyword, clean_name, punctuation=None):
        """To add one or more keywords to the dictionary
        pass the keyword and the clean name it maps to.
        Args:
            keyword : string
                keyword that you want to identify
            clean_name : string
                clean term for that keyword that you would want to get back in return or replace
                if not provided, keyword will be used as the clean name also.
            punctuation : list[char]
                list of punctuation characters to add to the keyword before adding.
        Returns:
            status : bool
                The return value. True for success, False otherwise.
        """
        return self.__setitem__(keyword, clean_name, punctuation)

    def replace_keywords(self, sentence):
        """Searches in the string for all keywords present in corpus.
        Keywords present are replaced by the clean name and a new string is returned.
        Args:
            sentence (str): Line of text where we will replace keywords
        Returns:
            new_sentence (str): Line of text with replaced keywords
        """
        if not sentence:
            # if sentence is empty or none just return the same.
            return sentence
        new_sentence = []
        orig_sentence = sentence
        if not self.case_sensitive:
            sentence = sentence.lower()
        current_word = ''
        current_dict = self.keyword_trie_dict
        sequence_end_pos = 0
        idx = 0
        sentence_len = len(sentence)
        while idx < sentence_len:
            char = sentence[idx]
            # when we reach whitespace
            if char not in self.non_word_boundaries:
                current_word += orig_sentence[idx]
                current_white_space = char
                # if end is present in current_dict
                if self._keyword in current_dict or char in current_dict:
                    # update longest sequence found
                    longest_sequence_found = None
                    is_longer_seq_found = False
                    if self._keyword in current_dict:
                        longest_sequence_found = current_dict[self._keyword]
                        sequence_end_pos = idx

                    # re look for longest_sequence from this position
                    if char in current_dict:
                        current_dict_continued = current_dict[char]
                        current_word_continued = current_word
                        idy = idx + 1
                        while idy < sentence_len:
                            inner_char = sentence[idy]
                            if inner_char not in self.non_word_boundaries and self._keyword in current_dict_continued:
                                current_word_continued += orig_sentence[idy]
                                # update longest sequence found
                                current_white_space = inner_char
                                longest_sequence_found = current_dict_continued[self._keyword]
                                sequence_end_pos = idy
                                is_longer_seq_found = True
                            if inner_char in current_dict_continued:
                                current_word_continued += orig_sentence[idy]
                                current_dict_continued = current_dict_continued[inner_char]
                            else:
                                break
                            idy += 1
                        else:
                            # end of sentence reached.
                            if self._keyword in current_dict_continued:
                                # update longest sequence found
                                current_white_space = ''
                                longest_sequence_found = current_dict_continued[self._keyword]
                                sequence_end_pos = idy
                                is_longer_seq_found = True
                        if is_longer_seq_found:
                            idx = sequence_end_pos
                            current_word = current_word_continued
                    current_dict = self.keyword_trie_dict
                    if longest_sequence_found:
                        new_sentence.append(longest_sequence_found + current_white_space)
                        current_word = ''
                    else:
                        new_sentence.append(current_word)
                        current_word = ''
                else:
                    # we reset current_dict
                    current_dict = self.keyword_trie_dict
                    new_sentence.append(current_word)
                    current_word = ''
            elif char in current_dict:
                # we can continue from this char
                current_word += orig_sentence[idx]
                current_dict = current_dict[char]
            else:
                current_word += orig_sentence[idx]
                # we reset current_dict
                current_dict = self.keyword_trie_dict
                # skip to end of word
                idy = idx + 1
                while idy < sentence_len:
                    char = sentence[idy]
                    current_word += orig_sentence[idy]
                    if char not in self.non_word_boundaries:
                        break
                    idy += 1
                idx = idy
                new_sentence.append(current_word)
                current_word = ''
            # if we are end of sentence and have a sequence discovered
            if idx + 1 >= sentence_len:
                if self._keyword in current_dict:
                    sequence_found = current_dict[self._keyword]
                    new_sentence.append(sequence_found)
                else:
                    new_sentence.append(current_word)
            idx += 1
        return "".join(new_sentence)


def file_to_list(filename, drop_first=True):
    items = []
    with open(filename, "r", encoding="utf-8") as f:
        if drop_first:
            f.readline()

        for line in f.readlines():
            items.append(line.rstrip())
    return items


def main():
    proc = KeywordProcessor()

    punctuation = ['.', ',', ' ', ':', ';', '?', '!', '']
    no_punctuation = ['']
    fields = {
        os.path.join('datasets', 'firstnames.csv'): {"replacement": "<NAAM>", "punctuation": punctuation},
        os.path.join('datasets', 'countries.csv'): {"replacement": "<LAND>", "punctuation": no_punctuation},
    }

    for field in fields:
        for name in file_to_list(field):
            proc.add_keyword(name, fields[field]["replacement"], punctuation)

    print(proc.replace_keywords("Leo."))
    print(proc.replace_keywords("Leopaart"))
    print(proc.replace_keywords(".Leo"))
    print(proc.replace_keywords(".Leo."))
    print(proc.replace_keywords("Leo"))


if __name__ == "__main__":
    main()
