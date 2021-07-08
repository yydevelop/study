# -*- coding: utf-8 -*-
"""proofread.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1nYq6yCMlqZcYI1uFET7-0S6eg-vXjMBe
"""

# Commented out IPython magic to ensure Python compatibility.
# 9-1
!mkdir proofread
# %cd ./proofread

# 9-2
!pip install transformers==4.5.0 fugashi==1.1.0 ipadic==1.0.0 pytorch-lightning==1.2.7

# 9-3
import random
from tqdm import tqdm
import unicodedata

import pandas as pd
import torch
from torch.utils.data import DataLoader
from transformers import BertJapaneseTokenizer, BertForMaskedLM
import pytorch_lightning as pl

# 日本語の事前学習済みモデル
MODEL_NAME = 'cl-tohoku/bert-base-japanese-whole-word-masking'

# 9-4
class SC_tokenizer(BertJapaneseTokenizer):
       
    def encode_plus_tagged(
        self, wrong_text, correct_text, max_length=128
    ):
        """
        ファインチューニング時に使用。
        誤変換を含む文章と正しい文章を入力とし、
        符号化を行いBERTに入力できる形式にする。
        """
        # 誤変換した文章をトークン化し、符号化
        encoding = tokenizer(
            wrong_text, 
            max_length=max_length, 
            padding='max_length', 
            truncation=True
        )
        # 正しい文章をトークン化し、符号化
        encoding_correct = tokenizer(
            correct_text,
            max_length=max_length,
            padding='max_length',
            truncation=True
        ) 
        # 正しい文章の符号をラベルとする
        encoding['labels'] = encoding_correct['input_ids'] 

        return encoding

    def encode_plus_untagged(
        self, text, max_length=None, return_tensors=None
    ):
        """
        文章を符号化し、それぞれのトークンの文章中の位置も特定しておく。
        """
        # 文章のトークン化を行い、
        # それぞれのトークンと文章中の文字列を対応づける。
        tokens = [] # トークンを追加していく。
        tokens_original = [] # トークンに対応する文章中の文字列を追加していく。
        words = self.word_tokenizer.tokenize(text) # MeCabで単語に分割
        for word in words:
            # 単語をサブワードに分割
            tokens_word = self.subword_tokenizer.tokenize(word) 
            tokens.extend(tokens_word)
            if tokens_word[0] == '[UNK]': # 未知語への対応
                tokens_original.append(word)
            else:
                tokens_original.extend([
                    token.replace('##','') for token in tokens_word
                ])

        # 各トークンの文章中での位置を調べる。（空白の位置を考慮する）
        position = 0
        spans = [] # トークンの位置を追加していく。
        for token in tokens_original:
            l = len(token)
            while 1:
                if token != text[position:position+l]:
                    position += 1
                else:
                    spans.append([position, position+l])
                    position += l
                    break

        # 符号化を行いBERTに入力できる形式にする。
        input_ids = tokenizer.convert_tokens_to_ids(tokens) 
        encoding = tokenizer.prepare_for_model(
            input_ids, 
            max_length=max_length, 
            padding='max_length' if max_length else False, 
            truncation=True if max_length else False
        )
        sequence_length = len(encoding['input_ids'])
        # 特殊トークン[CLS]に対するダミーのspanを追加。
        spans = [[-1, -1]] + spans[:sequence_length-2] 
        # 特殊トークン[SEP]、[PAD]に対するダミーのspanを追加。
        spans = spans + [[-1, -1]] * ( sequence_length - len(spans) ) 

        # 必要に応じてtorch.Tensorにする。
        if return_tensors == 'pt':
            encoding = { k: torch.tensor([v]) for k, v in encoding.items() }

        return encoding, spans

    def convert_bert_output_to_text(self, text, labels, spans):
        """
        推論時に使用。
        文章と、各トークンのラベルの予測値、文章中での位置を入力とする。
        そこから、BERTによって予測された文章に変換。
        """
        assert len(spans) == len(labels)

        # labels, spansから特殊トークンに対応する部分を取り除く
        labels = [label for label, span in zip(labels, spans) if span[0]!=-1]
        spans = [span for span in spans if span[0]!=-1]

        # BERTが予測した文章を作成
        predicted_text = ''
        position = 0
        for label, span in zip(labels, spans):
            start, end = span
            if position != start: # 空白の処理
                predicted_text += text[position:start]
            predicted_token = tokenizer.convert_ids_to_tokens(label)
            predicted_token = predicted_token.replace('##', '')
            predicted_token = unicodedata.normalize(
                'NFKC', predicted_token
            ) 
            predicted_text += predicted_token
            position = end
        
        return predicted_text

# 9-5
tokenizer = SC_tokenizer.from_pretrained(MODEL_NAME)

# 9-6
wrong_text = '優勝トロフィーを変換した'
correct_text = '優勝トロフィーを返還した'
encoding = tokenizer.encode_plus_tagged(
    wrong_text, correct_text, max_length=12
)
print(encoding)

# 9-7
wrong_text = '優勝トロフィーを変換した'
encoding, spans = tokenizer.encode_plus_untagged(
    wrong_text, return_tensors='pt'
)
print('# encoding')
print(encoding)
print('# spans')
print(spans)

# 9-8
predicted_labels = [2, 759, 18204, 11, 8274, 15, 10, 3]
predicted_text = tokenizer.convert_bert_output_to_text(
    wrong_text, predicted_labels, spans
)
print(predicted_text)

# 9-9
bert_mlm = BertForMaskedLM.from_pretrained(MODEL_NAME)
bert_mlm = bert_mlm.cuda()

# 9-10
text = '優勝トロフィーを変換した。'

# 符号化とともに各トークンの文章中の位置を計算しておく。
encoding, spans = tokenizer.encode_plus_untagged(
    text, return_tensors='pt'
)
encoding = { k: v.cuda() for k, v in encoding.items() }

# BERTに入力し、トークン毎にスコアの最も高いトークンのIDを予測値とする。
with torch.no_grad():
    output = bert_mlm(**encoding)
    scores = output.logits
    labels_predicted = scores[0].argmax(-1).cpu().numpy().tolist()
    
# ラベル列を文章に変換
predict_text = tokenizer.convert_bert_output_to_text(
    text, labels_predicted, spans
)

# 9-11
data = [
    {
        'wrong_text': '優勝トロフィーを変換した。',
        'correct_text': '優勝トロフィーを返還した。',
    },
    {
        'wrong_text': '人と森は強制している。',
        'correct_text': '人と森は共生している。',
    }
]

# 各データを符号化し、データローダへ入力できるようにする。
max_length=32
dataset_for_loader = []
for sample in data:
    wrong_text = sample['wrong_text']
    correct_text = sample['correct_text']
    encoding = tokenizer.encode_plus_tagged(
        wrong_text, correct_text, max_length=max_length
    )
    encoding = { k: torch.tensor(v) for k, v in encoding.items() }
    dataset_for_loader.append(encoding)

# データローダを作成
dataloader = DataLoader(dataset_for_loader, batch_size=2)

# ミニバッチをBERTへ入力し、損失を計算。
for batch in dataloader:
    encoding = { k: v.cuda() for k, v in batch.items() }
    output = bert_mlm(**encoding)
    loss = output.loss # 損失

# 9-12
!curl -L "https://nlp.ist.i.kyoto-u.ac.jp/DLcounter/lime.cgi?down=https://nlp.ist.i.kyoto-u.ac.jp/nl-resource/JWTD/jwtd.tar.gz&name=JWTD.tar.gz" -o JWTD.tar.gz
!tar zxvf JWTD.tar.gz

# 9-13
def create_dataset(data_df):

    tokenizer = SC_tokenizer.from_pretrained(MODEL_NAME)

    def check_token_count(row):
        """
        誤変換の文章と正しい文章でトークンに対応がつくかどうかを判定。
        （条件は上の文章を参照）
        """
        wrong_text_tokens = tokenizer.tokenize(row['wrong_text'])
        correct_text_tokens = tokenizer.tokenize(row['correct_text'])
        if len(wrong_text_tokens) != len(correct_text_tokens):
            return False
        
        diff_count = 0
        threthold_count = 2
        for wrong_text_token, correct_text_token \
            in zip(wrong_text_tokens, correct_text_tokens):

            if wrong_text_token != correct_text_token:
                diff_count += 1
                if diff_count > threthold_count:
                    return False
        return True

    def normalize(text):
        """
        文字列の正規化
        """
        text = text.strip()
        text = unicodedata.normalize('NFKC', text)
        return text

    # 漢字の誤変換のデータのみを抜き出す。
    category_type = 'kanji-conversion'
    data_df.query('category == @category_type', inplace=True) 
    data_df.rename(
        columns={'pre_text': 'wrong_text', 'post_text': 'correct_text'}, 
        inplace=True
    )
    
    # 誤変換と正しい文章をそれぞれ正規化し、
    # それらの間でトークン列に対応がつくもののみを抜き出す。
    data_df['wrong_text'] = data_df['wrong_text'].map(normalize) 
    data_df['correct_text'] = data_df['correct_text'].map(normalize)
    kanji_conversion_num = len(data_df)
    data_df = data_df[data_df.apply(check_token_count, axis=1)]
    same_tokens_count_num = len(data_df)
    print(
        f'- 漢字誤変換の総数：{kanji_conversion_num}',
        f'- トークンの対応関係のつく文章の総数: {same_tokens_count_num}',
        f'  (全体の{same_tokens_count_num/kanji_conversion_num*100:.0f}%)',
        sep = '\n'
    )
    return data_df[['wrong_text', 'correct_text']].to_dict(orient='records')

# データのロード
train_df = pd.read_json(
    './jwtd/train.jsonl', orient='records', lines=True
)
test_df = pd.read_json(
    './jwtd/test.jsonl', orient='records', lines=True
)

# 学習用と検証用データ
print('学習と検証用のデータセット：')
dataset = create_dataset(train_df)
random.shuffle(dataset)
n = len(dataset)
n_train = int(n*0.8)
dataset_train = dataset[:n_train]
dataset_val = dataset[n_train:]

# テストデータ
print('テスト用のデータセット：')
dataset_test = create_dataset(test_df)

# 9-14
def create_dataset_for_loader(tokenizer, dataset, max_length):
    """
    データセットをデータローダに入力可能な形式にする。
    """
    dataset_for_loader = []
    for sample in tqdm(dataset):
        wrong_text = sample['wrong_text']
        correct_text = sample['correct_text']
        encoding = tokenizer.encode_plus_tagged(
            wrong_text, correct_text, max_length=max_length
        )
        encoding = { k: torch.tensor(v) for k, v in encoding.items() }
        dataset_for_loader.append(encoding)
    return dataset_for_loader

tokenizer = SC_tokenizer.from_pretrained(MODEL_NAME)

# データセットの作成
max_length = 32
dataset_train_for_loader = create_dataset_for_loader(
    tokenizer, dataset_train, max_length
)
dataset_val_for_loader = create_dataset_for_loader(
    tokenizer, dataset_val, max_length
)

# データローダの作成
dataloader_train = DataLoader(
    dataset_train_for_loader, batch_size=32, shuffle=True
)
dataloader_val = DataLoader(dataset_val_for_loader, batch_size=256)

# 9-15
class BertForMaskedLM_pl(pl.LightningModule):
        
    def __init__(self, model_name, lr):
        super().__init__()
        self.save_hyperparameters()
        self.bert_mlm = BertForMaskedLM.from_pretrained(model_name)
        
    def training_step(self, batch, batch_idx):
        output = self.bert_mlm(**batch)
        loss = output.loss
        self.log('train_loss', loss)
        return loss
        
    def validation_step(self, batch, batch_idx):
        output = self.bert_mlm(**batch)
        val_loss = output.loss
        self.log('val_loss', val_loss)
   
    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.lr)

checkpoint = pl.callbacks.ModelCheckpoint(
    monitor='val_loss',
    mode='min',
    save_top_k=1,
    save_weights_only=True,
    dirpath='model/'
)

trainer = pl.Trainer(
    gpus=1,
    max_epochs=5,
    callbacks=[checkpoint]
)

# ファインチューニング
model = BertForMaskedLM_pl(MODEL_NAME, lr=1e-5)
trainer.fit(model, dataloader_train, dataloader_val)
best_model_path = checkpoint.best_model_path

# 9-16
def predict(text, tokenizer, bert_mlm):
    """
    文章を入力として受け、BERTが予測した文章を出力
    """
    # 符号化
    encoding, spans = tokenizer.encode_plus_untagged(
        text, return_tensors='pt'
    ) 
    encoding = { k: v.cuda() for k, v in encoding.items() }

    # ラベルの予測値の計算
    with torch.no_grad():
        output = bert_mlm(**encoding)
        scores = output.logits
        labels_predicted = scores[0].argmax(-1).cpu().numpy().tolist()

    # ラベル列を文章に変換
    predict_text = tokenizer.convert_bert_output_to_text(
        text, labels_predicted, spans
    )

    return predict_text

# いくつかの例に対してBERTによる文章校正を行ってみる。
text_list = [
    'ユーザーの試行に合わせた楽曲を配信する。',
    'メールに明日の会議の史料を添付した。',
    '乳酸菌で牛乳を発行するとヨーグルトができる。',
    '突然、子供が帰省を発した。'
]

# トークナイザ、ファインチューニング済みのモデルのロード
tokenizer = SC_tokenizer.from_pretrained(MODEL_NAME)
model = BertForMaskedLM_pl.load_from_checkpoint(best_model_path)
bert_mlm = model.bert_mlm.cuda()

for text in text_list:
    predict_text = predict(text, tokenizer, bert_mlm) # BERTによる予測
    print('---')
    print(f'入力：{text}')
    print(f'出力：{predict_text}')

# 9-17
# BERTで予測を行い、正解数を数える。
correct_num = 0 
for sample in tqdm(dataset_test):
    wrong_text = sample['wrong_text']
    correct_text = sample['correct_text']
    predict_text = predict(wrong_text, tokenizer, bert_mlm) # BERT予測
   
    if correct_text == predict_text: # 正解の場合
        correct_num += 1

print(f'Accuracy: {correct_num/len(dataset_test):.2f}')

# 9-18
correct_position_num = 0 # 正しく誤変換の漢字を特定できたデータの数
for sample in tqdm(dataset_test):
    wrong_text = sample['wrong_text']
    correct_text = sample['correct_text']
    
    # 符号化
    encoding = tokenizer(wrong_text)
    wrong_input_ids = encoding['input_ids'] # 誤変換の文の符合列
    encoding = {k: torch.tensor([v]).cuda() for k,v in encoding.items()}
    correct_encoding = tokenizer(correct_text)
    correct_input_ids = correct_encoding['input_ids'] # 正しい文の符合列
    
    # 文章を予測
    with torch.no_grad():
        output = bert_mlm(**encoding)
        scores = output.logits
        # 予測された文章のトークンのID
        predict_input_ids = scores[0].argmax(-1).cpu().numpy().tolist() 

    # 特殊トークンを取り除く
    wrong_input_ids = wrong_input_ids[1:-1]
    correct_input_ids =  correct_input_ids[1:-1]
    predict_input_ids =  predict_input_ids[1:-1]
    
    # 誤変換した漢字を特定できているかを判定
    # 符合列を比較する。
    detect_flag = True
    for wrong_token, correct_token, predict_token \
        in zip(wrong_input_ids, correct_input_ids, predict_input_ids):

        if wrong_token == correct_token: # 正しいトークン
            # 正しいトークンなのに誤って別のトークンに変換している場合
            if wrong_token != predict_token: 
                detect_flag = False
                break
        else: # 誤変換のトークン
            # 誤変換のトークンなのに、そのままにしている場合
            if wrong_token == predict_token: 
                detect_flag = False
                break

    if detect_flag: # 誤変換の漢字の位置を正しく特定できた場合
        correct_position_num += 1
        
print(f'Accuracy: {correct_position_num/len(dataset_test):.2f}')