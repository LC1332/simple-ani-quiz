export type Level = "easy" | "medium" | "hard";

export type NameOption = {
  character_id: number;
  name_cn: string;
  main_series: string;
};

export type ImageOption = {
  character_id: number;
  cos_image_id: number;
};

export type QuestionImageToName = {
  id: string;
  type: "image_to_name";
  cos_image_id: number;
  options: NameOption[];
  answer_character_id: number;
};

export type QuestionNameToImage = {
  id: string;
  type: "name_to_image";
  character_id: number;
  name_cn: string;
  main_series: string;
  options: ImageOption[];
  answer_character_id: number;
};

export type QuizQuestion = QuestionImageToName | QuestionNameToImage;

export type QuizResponse = {
  level: Level;
  questions: QuizQuestion[];
};
